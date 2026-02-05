#!/usr/bin/env python3
"""
pong.py - Classic Pong game for Display HAT Mini

Controls:
- Button A / Button B: Left player (up/down)
- Button X / Button Y: Right player (up/down)

Ported from Pimoroni's displayhatmini-python examples.
"""

import math
import random
import time
from collections import namedtuple

from displayhatmini_lite import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont


Position = namedtuple("Position", "x y")
Size = namedtuple("Size", "w h")


class Vec2D:
    """Simple 2D vector class (replaces turtle.Vec2D to avoid tkinter dependency)."""

    def __init__(self, x, y):
        self._x = float(x)
        self._y = float(y)

    def __getitem__(self, index):
        return (self._x, self._y)[index]

    def __add__(self, other):
        return Vec2D(self._x + other[0], self._y + other[1])

    def __mul__(self, scalar):
        return Vec2D(self._x * scalar, self._y * scalar)

    def __rmul__(self, scalar):
        return Vec2D(self._x * scalar, self._y * scalar)

    def __abs__(self):
        return math.sqrt(self._x ** 2 + self._y ** 2)

    def rotate(self, angle_degrees):
        """Rotate vector by angle in degrees."""
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return Vec2D(
            self._x * cos_a - self._y * sin_a,
            self._x * sin_a + self._y * cos_a
        )


def millis():
    return int(round(time.time() * 1000))


class Ball:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.position = Vec2D(width / 2, height / 2)
        self.velocity = Vec2D(0.15, 0.15)
        self.radius = 5
        self.color = (255, 255, 255)

    def reset(self):
        self.velocity = Vec2D(0.15, 0.15).rotate(random.randint(0, 360))
        self.position = Vec2D(self.width / 2, self.height / 2)

    @property
    def x(self):
        return self.position[0]

    @x.setter
    def x(self, value):
        self.position = Vec2D(value, self.position[1])

    @property
    def y(self):
        return self.position[1]

    @y.setter
    def y(self, value):
        self.position = Vec2D(self.position[0], value)

    @property
    def vx(self):
        return self.velocity[0]

    @vx.setter
    def vx(self, value):
        self.velocity = Vec2D(value, self.velocity[1])

    @property
    def vy(self):
        return self.velocity[1]

    @vy.setter
    def vy(self, value):
        self.velocity = Vec2D(self.velocity[0], value)

    @property
    def speed(self):
        return abs(self.velocity)

    def intersects(self, rect):
        rx, ry = rect.center
        rw, rh = rect.size

        dist_x = abs(self.x - rx)
        dist_y = abs(self.y - ry)

        if dist_x > rw / 2.0 + self.radius or dist_y > rh / 2.0 + self.radius:
            return False

        if dist_x <= rw / 2.0 or dist_y <= rh / 2.0:
            return True

        cx = dist_x - rw / 2.0
        cy = dist_y - rh / 2.0

        c_sq = cx**2.0 + cy**2.0

        return c_sq <= self.radius**2.0

    def update(self, delta, left_player, right_player):
        self.position += self.velocity * delta

        if (self.x < 50 and self.vx < 0) or (self.x > self.width - 50 and self.vx > 0):
            for item in [left_player, right_player]:
                if self.intersects(item):
                    item.success()

                    cx, cy = item.center
                    w, h = item.size
                    relative_y = (cy - self.y) / (h / 2)

                    speed = self.speed + (abs(relative_y) / 4)

                    angle = relative_y * 5 * (math.pi / 12)

                    if self.x > self.width / 2:
                        self.x = item.position.x - self.radius
                        self.velocity = Vec2D(
                            speed * -math.cos(angle), speed * -math.sin(angle)
                        )
                    else:
                        self.x = item.position.x + item.paddle_width + self.radius
                        self.velocity = Vec2D(
                            speed * math.cos(angle), speed * -math.sin(angle)
                        )

        if self.x - self.radius < 0 and self.vx < 0:
            left_player.fail()
            self.reset()

        elif self.x + self.radius > self.width and self.vx > 0:
            right_player.fail()
            self.reset()

        if self.y - self.radius < 0 and self.vy < 0:
            self.y = self.radius
            self.vy *= -1

        elif self.y + self.radius > self.height and self.vy > 0:
            self.y = self.height - self.radius
            self.vy *= -1

    def render(self, draw):
        draw.ellipse(
            (
                self.x - self.radius,
                self.y - self.radius,
                self.x + self.radius,
                self.y + self.radius,
            ),
            self.color,
        )


class Player:
    def __init__(self, side, width, height):
        self.score = 0
        self.screen_height = height
        self.y = height / 2
        self.next_y = self.y

        if side == 0:  # Left
            self.x = 25
        else:
            self.x = width - 25

        self.paddle_width = 5
        self.paddle_height = 50

    def paddle(self, y):
        self.next_y = y

    def success(self):
        self.score += 1

    def fail(self):
        self.score -= 1

    @property
    def center(self):
        return Position(x=self.x, y=self.y)

    @property
    def position(self):
        return Position(x=self.x - (self.paddle_width / 2), y=self.y - (self.paddle_height / 2))

    @property
    def size(self):
        return Size(w=self.paddle_width, h=self.paddle_height)

    def update(self):
        self.y = self.next_y

    def render(self, draw):
        draw.rectangle(
            (
                self.x - (self.paddle_width / 2),
                self.y - (self.paddle_height / 2),
                self.x + (self.paddle_width / 2),
                self.y + (self.paddle_height / 2),
            ),
            (255, 255, 255),
        )


def main():
    # Initialize display
    display = DisplayHATMini()
    display.set_backlight(1.0)
    display.set_led(0, 0, 0)

    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT

    # Create image buffer
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    # Initialize game objects
    player_one = Player(0, width, height)
    player_two = Player(1, width, height)
    ball = Ball(width, height)

    time_last = millis()
    paddle_speed = 15

    print("Pong - Display HAT Mini")
    print("Left player: A (up), B (down)")
    print("Right player: X (up), Y (down)")
    print("Press Ctrl+C to exit")

    try:
        while True:
            time_now = millis()
            time_delta = time_now - time_last

            # Handle input
            player_one_pos = player_one.center.y
            if display.read_button(DisplayHATMini.BUTTON_A):
                player_one_pos -= paddle_speed
            if display.read_button(DisplayHATMini.BUTTON_B):
                player_one_pos += paddle_speed

            player_two_pos = player_two.center.y
            if display.read_button(DisplayHATMini.BUTTON_X):
                player_two_pos -= paddle_speed
            if display.read_button(DisplayHATMini.BUTTON_Y):
                player_two_pos += paddle_speed

            # Clamp paddle positions
            player_one_pos = max(0, min(height, player_one_pos))
            player_two_pos = max(0, min(height, player_two_pos))

            player_one.paddle(player_one_pos)
            player_two.paddle(player_two_pos)

            # Clear screen
            draw.rectangle((0, 0, width, height), (0, 0, 0))

            # Draw center line
            draw.rectangle(
                ((width / 2) - 1, 20, (width / 2) + 1, height - 20), (64, 64, 64)
            )

            # Draw scores
            draw.text((25, 25), f"{player_one.score:02d}", fill=(255, 255, 255))
            draw.text((width - 45, 25), f"{player_two.score:02d}", fill=(255, 255, 255))

            # Update game state
            player_one.update()
            player_two.update()
            ball.update(time_delta, player_one, player_two)

            # Render
            ball.render(draw)
            player_one.render(draw)
            player_two.render(draw)

            # Send to display
            display.display(image)

            time.sleep(0.001)
            time_last = time_now

    except KeyboardInterrupt:
        print("\nGame over!")
        print(f"Final score: {player_one.score} - {player_two.score}")
        display.set_led(0, 0, 0)
        display.set_backlight(0)


if __name__ == "__main__":
    main()
