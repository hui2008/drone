# Raspberry Pi L298N Motor Driver Wiring

This design controls two DC motors from a Raspberry Pi through an L298N motor driver.

## Parts

- Raspberry Pi
- L298N motor driver module
- 1 or 2 DC motors
- External motor power supply
- Jumper wires

## Important Power Notes

- Do not power the motors from the Raspberry Pi 5V pin.
- Use a separate motor power supply connected to the L298N motor power input.
- Connect Raspberry Pi GND and L298N GND together.
- If your L298N board has `ENA` and `ENB` jumpers installed, remove them for PWM speed control.
- If the `ENA` and `ENB` jumpers stay installed, speed control is disabled and the motors run at full speed.

## Wiring Table

The Python script uses BCM GPIO numbering.

| L298N Pin | Raspberry Pi Pin | Purpose |
| --- | --- | --- |
| `GND` | `GND` | Shared ground |
| `+12V` / motor supply `+` | External motor supply `+` | Motor power input |
| `GND` / motor supply `-` | External motor supply `-` | Motor power return |
| `IN1` | `GPIO17` | Left motor direction |
| `IN2` | `GPIO27` | Left motor direction |
| `ENA` | `GPIO18` | Left motor PWM speed |
| `IN3` | `GPIO22` | Right motor direction |
| `IN4` | `GPIO23` | Right motor direction |
| `ENB` | `GPIO13` | Right motor PWM speed |
| `OUT1`, `OUT2` | Left DC motor | Left motor output |
| `OUT3`, `OUT4` | Right DC motor | Right motor output |

## Simple Wiring Diagram

```text
External motor supply +
        |
        v
   L298N +12V / motor supply input

External motor supply - ---- L298N GND ---- Raspberry Pi GND

Raspberry Pi GPIO17 ---- L298N IN1
Raspberry Pi GPIO27 ---- L298N IN2
Raspberry Pi GPIO18 ---- L298N ENA

Raspberry Pi GPIO22 ---- L298N IN3
Raspberry Pi GPIO23 ---- L298N IN4
Raspberry Pi GPIO13 ---- L298N ENB

L298N OUT1 ---- Left motor wire 1
L298N OUT2 ---- Left motor wire 2

L298N OUT3 ---- Right motor wire 1
L298N OUT4 ---- Right motor wire 2
```

## Software Setup

Install the Python GPIO libraries on the Raspberry Pi:

```bash
python3 -m pip install gpiozero lgpio
```

Run the motor test script from this folder:

```bash
python3 l298n_motor_control.py
```

Or from the project root:

```bash
python3 py/l298n_motor_control.py
```

## Direction Fixes

If a motor spins the wrong way, use one of these fixes:

- Swap the two motor wires on `OUT1` and `OUT2`, or `OUT3` and `OUT4`.
- Swap the matching GPIO assignments in `l298n_motor_control.py`.

## Troubleshooting

- Motor does not move: check external motor power and common ground.
- Motor only runs full speed: remove the `ENA` or `ENB` jumper and connect the PWM pin.
- Raspberry Pi resets: motor supply is causing voltage drop or noise; use a separate motor supply and common ground.
- One motor direction is wrong: swap that motor's output wires.
