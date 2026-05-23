"""
Drive two DC motors using:
    Raspberry Pi -> PCA9685 over I2C -> L298N motor driver.

Install on the Raspberry Pi:
    python3 -m pip install adafruit-circuitpython-pca9685

Enable I2C first:
    sudo raspi-config
    Interface Options -> I2C -> Enable

Run:
    python3 pca9685_l298n_two_motors.py
"""

from time import sleep

import board
import busio
from adafruit_pca9685 import PCA9685


# PCA9685 channel mapping.
# Change these if you wire the L298N to different PCA9685 channels.
MOTOR_A_ENA = 0
MOTOR_A_IN1 = 1
MOTOR_A_IN2 = 2

MOTOR_B_IN3 = 3
MOTOR_B_IN4 = 4
MOTOR_B_ENB = 5

PWM_OFF = 0x0000
PWM_ON = 0xFFFF


def notify(message: str) -> None:
    print(f"[motor-status] {message}", flush=True)


class L298NMotor:
    def __init__(self, pca: PCA9685, enable_channel: int, in_a_channel: int, in_b_channel: int):
        self.enable = pca.channels[enable_channel]
        self.in_a = pca.channels[in_a_channel]
        self.in_b = pca.channels[in_b_channel]
        self.stop()

    def _set_pin(self, channel, enabled: bool) -> None:
        channel.duty_cycle = PWM_ON if enabled else PWM_OFF

    def _set_speed(self, speed: float) -> None:
        speed = max(0.0, min(1.0, speed))
        self.enable.duty_cycle = int(speed * PWM_ON)

    def forward(self, speed: float = 0.6) -> None:
        self._set_pin(self.in_a, True)
        self._set_pin(self.in_b, False)
        self._set_speed(speed)

    def backward(self, speed: float = 0.6) -> None:
        self._set_pin(self.in_a, False)
        self._set_pin(self.in_b, True)
        self._set_speed(speed)

    def stop(self) -> None:
        self._set_speed(0.0)
        self._set_pin(self.in_a, False)
        self._set_pin(self.in_b, False)

    def brake(self) -> None:
        self._set_speed(0.0)
        self._set_pin(self.in_a, True)
        self._set_pin(self.in_b, True)


class TwoMotorDrive:
    def __init__(self, pca: PCA9685):
        self.left = L298NMotor(pca, MOTOR_A_ENA, MOTOR_A_IN1, MOTOR_A_IN2)
        self.right = L298NMotor(pca, MOTOR_B_ENB, MOTOR_B_IN3, MOTOR_B_IN4)

    def forward(self, speed: float = 0.6) -> None:
        self.left.forward(speed)
        self.right.forward(speed)

    def backward(self, speed: float = 0.6) -> None:
        self.left.backward(speed)
        self.right.backward(speed)

    def turn_left(self, speed: float = 0.6) -> None:
        self.left.backward(speed)
        self.right.forward(speed)

    def turn_right(self, speed: float = 0.6) -> None:
        self.left.forward(speed)
        self.right.backward(speed)

    def stop(self) -> None:
        self.left.stop()
        self.right.stop()


def main() -> None:
    notify("Starting PCA9685 L298N two-motor test")

    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c)
    pca.frequency = 1000
    notify("PCA9685 initialized at 1000 Hz")

    drive = TwoMotorDrive(pca)

    try:
        notify("Moving forward at 50% speed for 10 seconds")
        drive.forward(0.5)
        sleep(10)

        notify("Stopping for 5 seconds")
        drive.stop()
        sleep(5)

        notify("Moving backward at 50% speed for 10 seconds")
        drive.backward(0.5)
        sleep(10)

        notify("Stopping for 5 seconds")
        drive.stop()
        sleep(5)

        notify("Turning left at 50% speed for 10 seconds")
        drive.turn_left(0.5)
        sleep(10)

        notify("Turning right at 50% speed for 10 seconds")
        drive.turn_right(0.5)
        sleep(10)

        notify("Final stop")
        drive.stop()
    finally:
        notify("Cleaning up and disabling PCA9685 outputs")
        drive.stop()
        pca.deinit()
        notify("Done")


if __name__ == "__main__":
    main()
