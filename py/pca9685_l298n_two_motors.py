"""
Drive two DC motors using:
    Raspberry Pi -> PCA9685 over I2C -> L298N motor driver.

Install on the Raspberry Pi:
    python3 -m pip install adafruit-circuitpython-pca9685 rpi-lgpio

Enable I2C first:
    sudo raspi-config
    Interface Options -> I2C -> Enable

Run:
    python3 pca9685_l298n_two_motors.py
"""

from time import sleep

# board and busio are CircuitPython compatibility shims for Linux/Raspberry Pi.
# They expose the hardware I2C pins (SCL, SDA) as Python objects.
import board
import busio
from adafruit_pca9685 import PCA9685


# PCA9685 channel mapping.
# The PCA9685 is a 16-channel PWM controller connected to the Pi over I2C.
# Each channel below maps to one control wire on the L298N motor driver.
# Change these if you wire the L298N to different PCA9685 channels.
MOTOR_A_ENA = 0   # Channel 0: PWM speed control for motor A (ENA pin on L298N)
MOTOR_A_IN1 = 1   # Channel 1: direction bit 1 for motor A
MOTOR_A_IN2 = 2   # Channel 2: direction bit 2 for motor A

MOTOR_B_IN3 = 3   # Channel 3: direction bit 1 for motor B
MOTOR_B_IN4 = 4   # Channel 4: direction bit 2 for motor B
MOTOR_B_ENB = 5   # Channel 5: PWM speed control for motor B (ENB pin on L298N)

# The PCA9685 uses 16-bit duty cycle values.
# 0x0000 = 0% duty cycle (logic LOW), 0xFFFF = 100% duty cycle (logic HIGH).
PWM_OFF = 0x0000
PWM_ON = 0xFFFF


def notify(message: str) -> None:
    # Print status messages immediately (flush=True avoids buffering delays).
    print(f"[motor-status] {message}", flush=True)


class L298NMotor:
    """Controls a single DC motor through one half of an L298N H-bridge.

    The L298N H-bridge controls current direction through the motor using two
    direction pins (IN_A, IN_B) and one PWM enable pin (ENA/ENB):
        IN_A=HIGH, IN_B=LOW  -> motor spins forward
        IN_A=LOW,  IN_B=HIGH -> motor spins backward
        IN_A=LOW,  IN_B=LOW  -> motor coasts to a stop (no current)
        IN_A=HIGH, IN_B=HIGH -> motor brakes (both sides shorted together)
    Speed is set by varying the duty cycle on the enable pin via PWM.
    """

    def __init__(self, pca: PCA9685, enable_channel: int, in_a_channel: int, in_b_channel: int):
        # Grab references to the three PCA9685 channels used by this motor.
        self.enable = pca.channels[enable_channel]
        self.in_a = pca.channels[in_a_channel]
        self.in_b = pca.channels[in_b_channel]
        self.stop()  # Ensure the motor starts in a safe stopped state.

    def _set_pin(self, channel, enabled: bool) -> None:
        # Drive a direction pin fully HIGH or fully LOW (no PWM, just on/off).
        channel.duty_cycle = PWM_ON if enabled else PWM_OFF

    def _set_speed(self, speed: float) -> None:
        # Clamp speed to [0.0, 1.0] then scale to the 16-bit duty cycle range.
        speed = max(0.0, min(1.0, speed))
        self.enable.duty_cycle = int(speed * PWM_ON)

    def forward(self, speed: float = 0.6) -> None:
        # IN_A=HIGH, IN_B=LOW -> H-bridge drives current in the forward direction.
        self._set_pin(self.in_a, True)
        self._set_pin(self.in_b, False)
        self._set_speed(speed)

    def backward(self, speed: float = 0.6) -> None:
        # IN_A=LOW, IN_B=HIGH -> H-bridge reverses current direction.
        self._set_pin(self.in_a, False)
        self._set_pin(self.in_b, True)
        self._set_speed(speed)

    def stop(self) -> None:
        # Cut speed first, then float both direction pins -> motor coasts to rest.
        self._set_speed(0.0)
        self._set_pin(self.in_a, False)
        self._set_pin(self.in_b, False)

    def brake(self) -> None:
        # Both direction pins HIGH with zero duty cycle -> motor brakes hard
        # by short-circuiting the motor terminals through the H-bridge.
        self._set_speed(0.0)
        self._set_pin(self.in_a, True)
        self._set_pin(self.in_b, True)


class TwoMotorDrive:
    """High-level differential-drive abstraction over two L298NMotor instances.

    Turning is achieved by running the two motors in opposite directions
    (tank/skid-steer style), which pivots the chassis about its centre.
    """

    def __init__(self, pca: PCA9685):
        self.left = L298NMotor(pca, MOTOR_A_ENA, MOTOR_A_IN1, MOTOR_A_IN2)
        self.right = L298NMotor(pca, MOTOR_B_ENB, MOTOR_B_IN3, MOTOR_B_IN4)

    def forward(self, speed: float = 0.6) -> None:
        # Both motors spin forward -> robot drives straight ahead.
        self.left.forward(speed)
        self.right.forward(speed)

    def backward(self, speed: float = 0.6) -> None:
        # Both motors spin backward -> robot drives straight in reverse.
        self.left.backward(speed)
        self.right.backward(speed)

    def turn_left(self, speed: float = 0.6) -> None:
        # Left motor backward, right motor forward -> robot pivots left.
        self.left.backward(speed)
        self.right.forward(speed)

    def turn_right(self, speed: float = 0.6) -> None:
        # Left motor forward, right motor backward -> robot pivots right.
        self.left.forward(speed)
        self.right.backward(speed)

    def stop(self) -> None:
        self.left.stop()
        self.right.stop()


def main() -> None:
    notify("Starting PCA9685 L298N two-motor test")

    # Open the I2C bus using the Pi's hardware SCL/SDA pins, then initialise
    # the PCA9685 PWM controller at the default I2C address (0x40).
    i2c = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c)
    # 1000 Hz PWM frequency: fast enough for smooth DC motor speed control
    # without audible whine at very low frequencies.
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
        # The finally block guarantees motors are stopped and the PCA9685 outputs
        # are disabled even if an exception or KeyboardInterrupt occurs mid-run.
        notify("Cleaning up and disabling PCA9685 outputs")
        drive.stop()
        pca.deinit()
        notify("Done")


if __name__ == "__main__":
    main()
