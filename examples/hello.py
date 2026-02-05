#!/usr/bin/env python3
"""
hello.py - Basic Display HAT Mini test

Demonstrates:
- Display initialization
- Drawing text on screen
- RGB LED color cycling
- Backlight control
"""

import time

from displayhatmini_lite import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont


def main():
    # Initialize display
    display = DisplayHATMini()

    # Turn on backlight
    display.set_backlight(1.0)

    # Load a font
    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except OSError:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Create image and draw text
    image = Image.new("RGB", (DisplayHATMini.WIDTH, DisplayHATMini.HEIGHT), "black")
    draw = ImageDraw.Draw(image)

    draw.text((10, 30), "Display HAT Mini", font=font_large, fill="white")
    draw.text((10, 80), "luma.lcd edition", font=font_large, fill="cyan")
    draw.text((10, 140), "No NumPy required!", font=font_small, fill="lime")
    draw.text((10, 170), "Press Ctrl+C to exit", font=font_small, fill="gray")

    # Show on display
    display.display(image)

    # LED startup sequence
    colors = [
        (1, 0, 0),  # Red
        (0, 1, 0),  # Green
        (0, 0, 1),  # Blue
        (1, 1, 0),  # Yellow
        (0, 1, 1),  # Cyan
        (1, 0, 1),  # Magenta
        (1, 1, 1),  # White
        (0, 0, 0),  # Off
    ]

    print("Display HAT Mini - Hello World")
    print("LED cycling through colors...")
    print("Press Ctrl+C to exit")

    for r, g, b in colors:
        display.set_led(r, g, b)
        time.sleep(0.3)

    # Main loop - cycle LED
    try:
        while True:
            display.set_led(1, 0, 0)
            time.sleep(0.5)
            display.set_led(0, 1, 0)
            time.sleep(0.5)
            display.set_led(0, 0, 1)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nExiting...")
        display.set_led(0, 0, 0)
        display.set_backlight(0)


if __name__ == "__main__":
    main()
