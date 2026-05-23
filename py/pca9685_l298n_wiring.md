# Raspberry Pi PCA9685 L298N Two Motor Wiring

This setup uses the Raspberry Pi only for I2C. The PCA9685 outputs drive the L298N control pins.

## Raspberry Pi To PCA9685

| Raspberry Pi | PCA9685 |
| --- | --- |
| `3.3V` | `VCC` |
| `GND` | `GND` |
| `GPIO2` / `SDA` | `SDA` |
| `GPIO3` / `SCL` | `SCL` |

Use `VCC = 3.3V` for safe Raspberry Pi I2C logic.

## PCA9685 To L298N

The Python script uses these PCA9685 channels:

| PCA9685 Channel | L298N Pin | Purpose |
| --- | --- | --- |
| `0` | `ENA` | Motor A speed |
| `1` | `IN1` | Motor A direction |
| `2` | `IN2` | Motor A direction |
| `3` | `IN3` | Motor B direction |
| `4` | `IN4` | Motor B direction |
| `5` | `ENB` | Motor B speed |

Remove the L298N `ENA` and `ENB` jumpers so the PCA9685 can control speed.

## Motors And Power

Use this power setup:

- L298N motor power comes from a 2S LiPo.
- L298N `5V_EN` jumper stays installed.
- Raspberry Pi is powered from its own regulated 5V supply.
- Raspberry Pi, PCA9685, L298N, and LiPo grounds must be connected together.

| Part / Pin | Connect To |
| --- | --- |
| `OUT1`, `OUT2` | Motor A |
| `OUT3`, `OUT4` | Motor B |
| L298N `+12V` / `VMS` / motor input | 2S LiPo `+` |
| L298N `GND` | 2S LiPo `-` |
| L298N `GND` | Raspberry Pi/PCA9685 common ground |
| Raspberry Pi power input | Separate regulated 5V supply |

With the L298N `5V_EN` jumper installed, the L298N onboard regulator powers the L298N logic from the 2S LiPo input.

Do not connect the 2S LiPo directly to the Raspberry Pi power input. Do not power the motors from the Raspberry Pi 5V pin.

## Ground Connection

All grounds must be common:

```text
2S LiPo - ---- L298N GND ---- PCA9685 GND ---- Raspberry Pi GND
```

## Install

Enable I2C:

```bash
sudo raspi-config
```

Then install the Python library:

```bash
python3 -m pip install adafruit-circuitpython-pca9685
```

## Run

```bash
python3 py/pca9685_l298n_two_motors.py
```

## Expected Test

The script will:

1. Drive both motors forward.
2. Stop.
3. Drive both motors backward.
4. Stop.
5. Turn left.
6. Turn right.
7. Stop.
