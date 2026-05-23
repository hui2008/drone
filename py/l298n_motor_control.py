"""
Control one or two DC motors through an L298N driver from a Raspberry Pi.

Install dependencies on the Raspberry Pi:
    python3 -m pip install gpiozero lgpio

Wiring notes:
    Raspberry Pi GND must connect to L298N GND.
    Use a separate motor power supply; do not power motors from the Pi 5V pin.
    Remove ENA/ENB jumpers if you want PWM speed control.
"""

from time import sleep

from gpiozero import Motor, PWMOutputDevice


# Change these BCM GPIO pin numbers to match your wiring.
LEFT_IN1 = 17
LEFT_IN2 = 27
LEFT_ENA = 18

RIGHT_IN3 = 22
RIGHT_IN4 = 23
RIGHT_ENB = 13


left_motor = Motor(forward=LEFT_IN1, backward=LEFT_IN2)
right_motor = Motor(forward=RIGHT_IN3, backward=RIGHT_IN4)

left_speed = PWMOutputDevice(LEFT_ENA)
right_speed = PWMOutputDevice(RIGHT_ENB)


def set_speed(left: float, right: float) -> None:
    """Set motor speed from 0.0 to 1.0."""
    left_speed.value = max(0.0, min(1.0, left))
    right_speed.value = max(0.0, min(1.0, right))


def forward(speed: float = 0.6) -> None:
    set_speed(speed, speed)
    left_motor.forward()
    right_motor.forward()


def backward(speed: float = 0.6) -> None:
    set_speed(speed, speed)
    left_motor.backward()
    right_motor.backward()


def turn_left(speed: float = 0.6) -> None:
    set_speed(speed, speed)
    left_motor.backward()
    right_motor.forward()


def turn_right(speed: float = 0.6) -> None:
    set_speed(speed, speed)
    left_motor.forward()
    right_motor.backward()


def stop() -> None:
    left_motor.stop()
    right_motor.stop()
    set_speed(0.0, 0.0)


def cleanup() -> None:
    stop()
    left_motor.close()
    right_motor.close()
    left_speed.close()
    right_speed.close()


if __name__ == "__main__":
    try:
        forward(0.6)
        sleep(2)

        backward(0.6)
        sleep(2)

        turn_left(0.6)
        sleep(1)

        turn_right(0.6)
        sleep(1)

        stop()
    finally:
        cleanup()
