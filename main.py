# SPDX-FileCopyrightText: Combined example for Adafruit Industries
# SPDX-License-Identifier: MIT

# This example displays a clock with date and allows scrolling to see the IP address.
# Use the Up/Down buttons to switch between views.
# Press B (D6) to start/stop a Pong game.

import fcntl
import random
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

button_A = DigitalInOut(board.D5)
button_A.direction = Direction.INPUT
button_A.pull = Pull.UP

button_B = DigitalInOut(board.D6)
button_B.direction = Direction.INPUT
button_B.pull = Pull.UP

button_L = DigitalInOut(board.D27)
button_L.direction = Direction.INPUT
button_L.pull = Pull.UP

button_R = DigitalInOut(board.D23)
button_R.direction = Direction.INPUT
button_R.pull = Pull.UP

button_C = DigitalInOut(board.D4)
button_C.direction = Direction.INPUT
button_C.pull = Pull.UP

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
font_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)

# View state: 0 = clock/date, 1 = IP address
current_view = 0
NUM_VIEWS = 2

# Button state tracking for edge detection
last_button_u = True
last_button_d = True
last_button_a = True
last_button_b = True
last_button_l = True
last_button_r = True
last_button_c = True

# Name display mode (toggled by button A/D5)
name_mode = False

# Pong game state
pong_mode = False
pong_game_over = False
pong_score = 0

# Pong game constants
PADDLE_WIDTH = 3
PADDLE_HEIGHT = 16
PADDLE_LEFT_X = 2
PADDLE_RIGHT_X = 128 - PADDLE_WIDTH - 2
BALL_RADIUS = 3

# Pong game variables
paddle_left_y = 0
paddle_right_y = 0
ball_x = 0.0
ball_y = 0.0
ball_dx = 0.0
ball_dy = 0.0
ball_speed = 2.0  # Base speed multiplier


def reset_pong_game():
    """Initialize or reset the pong game state."""
    global paddle_left_y, paddle_right_y, ball_x, ball_y, ball_dx, ball_dy, ball_speed
    global pong_game_over, pong_score

    paddle_left_y = (oled.height - PADDLE_HEIGHT) // 2
    paddle_right_y = (oled.height - PADDLE_HEIGHT) // 2
    ball_x = oled.width // 2
    ball_y = oled.height // 2
    # Random initial direction
    ball_dx = ball_speed * random.choice([1, -1])
    ball_dy = ball_speed * random.choice([0.5, -0.5, 1, -1])
    pong_game_over = False
    pong_score = 0


def update_pong_game():
    """Update the pong game logic."""
    global ball_x, ball_y, ball_dx, ball_dy, pong_game_over, pong_score

    if pong_game_over:
        return

    # Move ball
    ball_x += ball_dx
    ball_y += ball_dy

    # Ball collision with top and bottom walls
    if ball_y <= BALL_RADIUS:
        ball_y = BALL_RADIUS
        ball_dy = -ball_dy
    elif ball_y >= oled.height - BALL_RADIUS:
        ball_y = oled.height - BALL_RADIUS
        ball_dy = -ball_dy

    # Ball collision with left paddle
    if ball_x - BALL_RADIUS <= PADDLE_LEFT_X + PADDLE_WIDTH:
        if paddle_left_y <= ball_y <= paddle_left_y + PADDLE_HEIGHT:
            # Ball hits left paddle - bounce back
            ball_x = PADDLE_LEFT_X + PADDLE_WIDTH + BALL_RADIUS
            ball_dx = abs(ball_dx)  # Ensure ball goes right
            # Randomize y-axis speed
            ball_dy = random.uniform(-3, 3)
            # Add score based on current speed
            pong_score += int(ball_speed)
        elif ball_x - BALL_RADIUS <= 0:
            # Ball passed the left paddle - game over
            pong_game_over = True

    # Ball collision with right paddle
    if ball_x + BALL_RADIUS >= PADDLE_RIGHT_X:
        if paddle_right_y <= ball_y <= paddle_right_y + PADDLE_HEIGHT:
            # Ball hits right paddle - bounce back
            ball_x = PADDLE_RIGHT_X - BALL_RADIUS
            ball_dx = -abs(ball_dx)  # Ensure ball goes left
            # Randomize y-axis speed
            ball_dy = random.uniform(-3, 3)
            # Add score based on current speed
            pong_score += int(ball_speed)
        elif ball_x + BALL_RADIUS >= oled.width:
            # Ball passed the right paddle - game over
            pong_game_over = True


def draw_pong_game():
    """Draw the pong game view."""
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

    if pong_game_over:
        # Game over screen
        draw.text((20, 10), "GAME OVER", font=font_medium, fill=255)
        draw.text((20, 30), f"Score: {pong_score}", font=font_small, fill=255)
        draw.text((10, 48), "Press C/D4 to restart", font=font_tiny, fill=255)
    else:
        # Draw left paddle
        draw.rectangle(
            (
                PADDLE_LEFT_X,
                paddle_left_y,
                PADDLE_LEFT_X + PADDLE_WIDTH,
                paddle_left_y + PADDLE_HEIGHT,
            ),
            outline=255,
            fill=255,
        )

        # Draw right paddle
        draw.rectangle(
            (
                PADDLE_RIGHT_X,
                paddle_right_y,
                PADDLE_RIGHT_X + PADDLE_WIDTH,
                paddle_right_y + PADDLE_HEIGHT,
            ),
            outline=255,
            fill=255,
        )

        # Draw ball (circle/ellipse)
        draw.ellipse(
            (
                int(ball_x) - BALL_RADIUS,
                int(ball_y) - BALL_RADIUS,
                int(ball_x) + BALL_RADIUS,
                int(ball_y) + BALL_RADIUS,
            ),
            outline=255,
            fill=255,
        )

        # Draw score at top center
        score_text = f"{pong_score}"
        bbox = draw.textbbox((0, 0), score_text, font=font_tiny)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(
            ((oled.width - text_width) // 2, oled.height - text_height - 2),
            score_text,
            font=font_tiny,
            fill=255,
        )

        # Draw speed indicator at top center
        speed_text = f"Spd:{ball_speed:.0f}"
        bbox = draw.textbbox((0, 0), speed_text, font=font_tiny)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((oled.width - text_width) // 2, 2), speed_text, font=font_tiny, fill=255
        )


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


def draw_name_view():
    """Draw name based on day of year: Matheo if odd, Nuria if even."""
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)

    # Get day of year (1-366)
    day_of_year = int(time.strftime("%j"))

    if day_of_year % 2 == 1:  # Odd day
        name = "Nuria"
    else:  # Even day
        name = "Matheo"

    # Center the name on the display
    bbox = draw.textbbox((0, 0), name, font=font_huge)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (oled.width - text_width) // 2
    y = (oled.height - text_height) // 2

    draw.text((x, y), name, font=font_huge, fill=255)


def update_display():
    """Update the display based on current view."""
    if pong_mode:
        update_pong_game()
        draw_pong_game()
    elif name_mode:
        draw_name_view()
    elif current_view == 0:
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
    button_a_pressed = not button_A.value
    button_b_pressed = not button_B.value
    button_l_pressed = not button_L.value
    button_r_pressed = not button_R.value
    button_c_pressed = not button_C.value

    # Detect button press (falling edge)
    if button_b_pressed and last_button_b:
        # Button B (D6) pressed - toggle pong mode
        pong_mode = not pong_mode
        if pong_mode:
            reset_pong_game()

    if pong_mode:
        # Pong game controls
        if button_u_pressed:
            # Move both paddles up
            paddle_left_y = max(0, paddle_left_y - 8)
            paddle_right_y = max(0, paddle_right_y - 8)

        if button_d_pressed:
            # Move both paddles down
            paddle_left_y = min(oled.height - PADDLE_HEIGHT, paddle_left_y + 8)
            paddle_right_y = min(oled.height - PADDLE_HEIGHT, paddle_right_y + 8)

        if button_l_pressed and last_button_l:
            # Decrease ball speed
            ball_speed = max(1, ball_speed - 1)
            # Update ball velocity to new speed while keeping direction
            if ball_dx != 0:
                ball_dx = ball_speed * (1 if ball_dx > 0 else -1)

        if button_r_pressed and last_button_r:
            # Increase ball speed (no upper limit)
            ball_speed += 1
            # Update ball velocity to new speed while keeping direction
            if ball_dx != 0:
                ball_dx = ball_speed * (1 if ball_dx > 0 else -1)

        if button_c_pressed and last_button_c and pong_game_over:
            # Button C (D4) pressed - restart game when game over
            reset_pong_game()
    else:
        # Normal mode controls
        if button_u_pressed and last_button_u:
            # Up button pressed - go to previous view
            current_view = (current_view - 1) % NUM_VIEWS

        if button_d_pressed and last_button_d:
            # Down button pressed - go to next view
            current_view = (current_view + 1) % NUM_VIEWS

        if button_a_pressed and last_button_a:
            # Button A (D5) pressed - toggle name mode
            name_mode = not name_mode

    # Update button state tracking
    last_button_u = not button_u_pressed
    last_button_d = not button_d_pressed
    last_button_a = not button_a_pressed
    last_button_b = not button_b_pressed
    last_button_l = not button_l_pressed
    last_button_r = not button_r_pressed
    last_button_c = not button_c_pressed

    # Update the display
    update_display()

    # Small delay to prevent excessive CPU usage
    time.sleep(0.05 if pong_mode else 0.1)
