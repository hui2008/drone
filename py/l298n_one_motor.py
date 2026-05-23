"""
Baby-step test: control one DC motor through an L298N from a Raspberry Pi.

Install on the Raspberry Pi:
    python3 -m pip install gpiozero lgpio

Run:
    python3 l298n_one_motor.py
"""

from time import sleep

from gpiozero import Motor, PWMOutputDevice


# BCM GPIO pin numbers. Change these if your wiring is different.
ENA = 17
IN1 = 27
IN2 = 22


motor = Motor(forward=IN1, backward=IN2)
speed = PWMOutputDevice(ENA)


def set_speed(value: float) -> None:
    """Set motor speed from 0.0 to 1.0."""
    speed.value = max(0.0, min(1.0, value))


def stop() -> None:
    motor.stop()
    set_speed(0.0)


if __name__ == "__main__":
    try:
        set_speed(0.5)

        motor.forward()
        sleep(30)

        stop()
        sleep(10)

        motor.backward()
        sleep(30)

        stop()
    finally:
        stop()
        motor.close()
        speed.close()
