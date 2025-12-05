# SPDX-FileCopyrightText: Combined example for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example displays a clock with date and allows scrolling to see the IP address.
# Use the Up/Down buttons to switch between views.

import fcntl
import socket
import struct
import time

import adafruit_ssd1306
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from PIL import Image, ImageDraw, ImageFont


def get_ip_address(ifname):
    """Get the IP address of a network interface."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", str.encode(ifname[:15])),
        )[20:24]
    )


def get_current_ip():
    """Try to get the current IP address from wlan0 or eth0."""
    try:
        return get_ip_address("wlan0")
    except OSError:
        try:
            return get_ip_address("eth0")
        except OSError:
            return "NO INTERNET!"


# Create the I2C interface
i2c = busio.I2C(board.SCL, board.SDA)

# Create the SSD1306 OLED class (128x64 pixels)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Setup button inputs for scrolling (active low with pull-up)
button_U = DigitalInOut(board.D17)
button_U.direction = Direction.INPUT
button_U.pull = Pull.UP

button_D = DigitalInOut(board.D22)
button_D.direction = Direction.INPUT
button_D.pull = Pull.UP

# Clear display
oled.fill(0)
oled.show()

# Create blank image for drawing
image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)

# Load fonts
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

# View state: 0 = clock/date, 1 = IP address
current_view = 0
NUM_VIEWS = 2

# Button state tracking for edge detection
last_button_u = True
last_button_d = True


def draw_clock_view():
    """Draw the clock and date view."""
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

    # Day of week
    text = time.strftime("%A")
    draw.text((0, 0), text, font=font_medium, fill=255)

    # Date
    text = time.strftime("%e %b %Y")
    draw.text((0, 14), text, font=font_medium, fill=255)

    # Time
    text = time.strftime("%X")
    draw.text((0, 36), text, font=font_large, fill=255)


def draw_ip_view():
    """Draw the IP address view."""
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

    # Title
    draw.text((0, 0), "IP Address:", font=font_medium, fill=255)

    # IP address
    ip = get_current_ip()
    draw.text((0, 24), ip, font=font_small, fill=255)

    # Network interfaces hint
    draw.text((0, 48), "wlan0 / eth0", font=font_small, fill=255)


def update_display():
    """Update the display based on current view."""
    if current_view == 0:
        draw_clock_view()
    elif current_view == 1:
        draw_ip_view()

    oled.image(image)
    oled.show()


# Main loop
while True:
    # Read button states (active low)
    button_u_pressed = not button_U.value
    button_d_pressed = not button_D.value

    # Detect button press (falling edge)
    if button_u_pressed and last_button_u:
        # Up button pressed - go to previous view
        current_view = (current_view - 1) % NUM_VIEWS

    if button_d_pressed and last_button_d:
        # Down button pressed - go to next view
        current_view = (current_view + 1) % NUM_VIEWS

    # Update button state tracking
    last_button_u = not button_u_pressed
    last_button_d = not button_d_pressed

    # Update the display
    update_display()

    # Small delay to prevent excessive CPU usage
    time.sleep(0.1)
