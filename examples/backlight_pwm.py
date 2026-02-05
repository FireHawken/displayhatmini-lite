#!/usr/bin/env python3
"""
backlight_pwm.py - Backlight brightness control demo

Controls:
- Button A: Increase brightness
- Button B: Decrease brightness

Demonstrates PWM backlight dimming on Display HAT Mini.
"""

import time

from displayhatmini_lite import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont


def main():
    # Initialize display with PWM backlight enabled
    display = DisplayHATMini(backlight_pwm=True)

    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT

    # Create image buffer
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Load font
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except OSError:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    brightness = 1.0
    brightness_step = 0.1

    print("Backlight PWM Demo")
    print("Button A: Brighter")
    print("Button B: Dimmer")
    print("Press Ctrl+C to exit")

    try:
        while True:
            # Check buttons
            if display.read_button(DisplayHATMini.BUTTON_A):
                brightness = min(1.0, brightness + brightness_step)
                time.sleep(0.1)  # Debounce

            if display.read_button(DisplayHATMini.BUTTON_B):
                brightness = max(0.0, brightness - brightness_step)
                time.sleep(0.1)  # Debounce

            # Apply brightness
            display.set_backlight(brightness)

            # Clear and redraw
            draw.rectangle((0, 0, width, height), "white")

            draw.text((20, 40), "Backlight Control", font=font, fill="black")
            draw.text((20, 80), f"Brightness: {brightness:.0%}", font=font, fill="black")

            draw.text((20, 140), "A = Brighter", font=font_small, fill="darkgreen")
            draw.text((20, 170), "B = Dimmer", font=font_small, fill="darkred")

            # Draw brightness bar
            bar_x = 20
            bar_y = 200
            bar_width = 280
            bar_height = 20

            draw.rectangle(
                (bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
                outline="black",
                fill="lightgray",
            )
            draw.rectangle(
                (bar_x, bar_y, bar_x + int(bar_width * brightness), bar_y + bar_height),
                fill="blue",
            )

            # Send to display
            display.display(image)

            time.sleep(0.03)  # ~30 FPS

    except KeyboardInterrupt:
        print("\nExiting...")
        display.set_backlight(0)
        display.set_led(0, 0, 0)


if __name__ == "__main__":
    main()
