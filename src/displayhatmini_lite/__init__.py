"""
displayhatmini_lite - Lightweight driver for Pimoroni Display HAT Mini

A NumPy-free replacement for the official displayhatmini library,
using luma.lcd for display communication.
"""

__version__ = "0.1.1"

import atexit

import RPi.GPIO as GPIO
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image


class DisplayHATMini:
    """
    Driver for the Pimoroni Display HAT Mini.

    A 320x240 IPS display with RGB backlight LED and four buttons.

    Args:
        backlight_pwm: If True, use PWM for dimmable backlight.
                      If False (default), use simple on/off control.
    """

    # Button GPIO pins (active low with pull-up)
    BUTTON_A = 5
    BUTTON_B = 6
    BUTTON_X = 16
    BUTTON_Y = 24

    # RGB LED GPIO pins (active low - inverted logic)
    LED_R = 17
    LED_G = 27
    LED_B = 22

    # Display configuration
    SPI_PORT = 0
    SPI_CS = 1  # CE1
    SPI_DC = 9
    BACKLIGHT = 13

    # Display dimensions
    WIDTH = 320
    HEIGHT = 240

    # PWM frequency
    LED_PWM_FREQ = 2000
    BACKLIGHT_PWM_FREQ = 500

    # SPI speed - 80 MHz works reliably and gives good performance
    SPI_SPEED_HZ = 80_000_000  # 80 MHz

    def __init__(self, backlight_pwm: bool = False, spi_speed_hz: int = None):
        """
        Initialize the Display HAT Mini.

        Args:
            backlight_pwm: If True, use PWM for dimmable backlight.
            spi_speed_hz: SPI bus speed in Hz. Default 80 MHz for best performance.
                         Can try 100_000_000 for ~20 FPS if display is stable.
        """
        self._backlight_pwm_enabled = backlight_pwm
        self._spi_speed = spi_speed_hz or self.SPI_SPEED_HZ
        self._button_callback = None

        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Set up buttons with pull-up resistors
        for pin in (self.BUTTON_A, self.BUTTON_B, self.BUTTON_X, self.BUTTON_Y):
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Set up RGB LED with PWM
        self._led_pwm = {}
        for pin in (self.LED_R, self.LED_G, self.LED_B):
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, self.LED_PWM_FREQ)
            pwm.start(100)  # Start at 100% duty = LED off (inverted)
            self._led_pwm[pin] = pwm

        # Set up backlight
        GPIO.setup(self.BACKLIGHT, GPIO.OUT)
        if backlight_pwm:
            self._backlight_pwm = GPIO.PWM(self.BACKLIGHT, self.BACKLIGHT_PWM_FREQ)
            self._backlight_pwm.start(100)  # Full brightness
        else:
            self._backlight_pwm = None
            GPIO.output(self.BACKLIGHT, GPIO.HIGH)

        # Initialize display via luma.lcd
        # Use 52 MHz initially (luma's max allowed), then override if higher requested
        initial_speed = min(self._spi_speed, 52_000_000)
        serial = spi(
            port=self.SPI_PORT,
            device=self.SPI_CS,
            gpio_DC=self.SPI_DC,
            gpio_RST=None,
            bus_speed_hz=initial_speed,
        )

        # Override SPI speed if higher than luma's whitelist allows
        if self._spi_speed > 52_000_000:
            serial._spi.max_speed_hz = self._spi_speed

        self._device = st7789(
            serial,
            width=self.WIDTH,
            height=self.HEIGHT,
            rotate=2,  # 180 degree rotation for correct orientation
        )

        # Register cleanup on exit
        atexit.register(self._cleanup)

    def set_led(self, r: float = 0.0, g: float = 0.0, b: float = 0.0) -> None:
        """
        Set the RGB LED color.

        Args:
            r: Red intensity (0.0 to 1.0)
            g: Green intensity (0.0 to 1.0)
            b: Blue intensity (0.0 to 1.0)

        Raises:
            ValueError: If any value is outside the 0.0-1.0 range.
        """
        for name, value in [("r", r), ("g", g), ("b", b)]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0 (got {value})")

        # Inverted logic: 100% duty = off, 0% duty = full brightness
        self._led_pwm[self.LED_R].ChangeDutyCycle((1.0 - r) * 100)
        self._led_pwm[self.LED_G].ChangeDutyCycle((1.0 - g) * 100)
        self._led_pwm[self.LED_B].ChangeDutyCycle((1.0 - b) * 100)

    def set_backlight(self, value: float) -> None:
        """
        Set the backlight brightness.

        Args:
            value: Brightness level (0.0 = off, 1.0 = full brightness)

        Raises:
            ValueError: If value is outside the 0.0-1.0 range.
        """
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Backlight value must be between 0.0 and 1.0 (got {value})")

        if self._backlight_pwm:
            self._backlight_pwm.ChangeDutyCycle(value * 100)
        else:
            GPIO.output(self.BACKLIGHT, GPIO.HIGH if value > 0 else GPIO.LOW)

    def display(self, image: Image.Image) -> None:
        """
        Display a PIL Image on the screen.

        Args:
            image: A PIL Image object. Should be 320x240 RGB.
                  Will be converted/resized if necessary.

        Note:
            For best performance, pass images that are already 320x240 RGB
            to avoid conversion overhead.
        """
        self._device.display(image)

    def on_button_pressed(self, callback) -> None:
        """
        Register a callback for button events.

        The callback receives the GPIO pin number as its argument.
        Called on both press and release events.

        Args:
            callback: Function that takes one argument (pin number).
                     Use read_button(pin) inside to check state.
        """
        self._button_callback = callback

        for pin in (self.BUTTON_A, self.BUTTON_B, self.BUTTON_X, self.BUTTON_Y):
            # Remove any existing event detection
            try:
                GPIO.remove_event_detect(pin)
            except RuntimeError:
                pass

            # Add edge detection for both press and release
            GPIO.add_event_detect(
                pin,
                GPIO.BOTH,
                callback=self._handle_button,
                bouncetime=10
            )

    def _handle_button(self, pin: int) -> None:
        """Internal button event handler."""
        if self._button_callback:
            self._button_callback(pin)

    def read_button(self, pin: int) -> bool:
        """
        Read the current state of a button.

        Args:
            pin: The GPIO pin number (use BUTTON_A, BUTTON_B, etc.)

        Returns:
            True if the button is currently pressed, False otherwise.
        """
        # Buttons are active low (pressed = LOW)
        return not GPIO.input(pin)

    def _cleanup(self) -> None:
        """Clean up GPIO resources."""
        # Stop PWM
        for pwm in self._led_pwm.values():
            pwm.stop()
        if self._backlight_pwm:
            self._backlight_pwm.stop()

        # Turn off LED and backlight
        for pin in (self.LED_R, self.LED_G, self.LED_B):
            GPIO.output(pin, GPIO.HIGH)  # LED off
        GPIO.output(self.BACKLIGHT, GPIO.LOW)  # Backlight off

    def __del__(self):
        """Destructor - clean up resources."""
        try:
            self._cleanup()
        except Exception:
            pass  # Ignore errors during cleanup
