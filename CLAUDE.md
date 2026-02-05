# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`displayhatmini-lite` is a lightweight, NumPy-free Python driver for the Pimoroni Display HAT Mini. It's a drop-in replacement for the official `displayhatmini` library, built on `luma.lcd` instead of NumPy-dependent `st7789`.

## Build & Development Commands

```bash
# Install in development mode
pip install -e .

# Build distribution
python -m build

# Upload to PyPI (test)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*

# Run example on Raspberry Pi
python examples/hello.py
```

## Project Structure

```
displayhatmini-lite/
├── src/displayhatmini_lite/    # Main package
│   └── __init__.py             # DisplayHATMini class
├── examples/                    # Example scripts
│   ├── hello.py
│   ├── pong.py
│   └── backlight_pwm.py
├── pyproject.toml              # Package metadata & dependencies
└── README.md
```

## Architecture

The library provides a single `DisplayHATMini` class that:
- Uses `luma.lcd` for ST7789 display communication (no NumPy)
- Uses `RPi.GPIO` for button input and RGB LED PWM control
- Accepts PIL `Image` objects for display (not numpy arrays)

Key difference from original: the `display()` method takes a PIL Image directly, not a numpy buffer.

## Hardware Pins (BCM)

- Display: SPI0.1 (CE1=7, DC=9, MOSI=10, SCLK=11)
- Backlight: GPIO 13
- RGB LED: R=17, G=27, B=22
- Buttons: A=5, B=6, X=16, Y=24

## Dependencies

Runtime: `luma.lcd`, `RPi.GPIO`, `Pillow`, `spidev`
Build: `build`, `twine`
