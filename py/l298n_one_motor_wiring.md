# Raspberry Pi L298N One Motor Test

This is the first baby-step test: one Raspberry Pi controls one DC motor through one side of the L298N.

## Wiring

The Python script uses BCM GPIO numbering.

| L298N Pin | Connect To | Purpose |
| --- | --- | --- |
| `IN1` | Raspberry Pi `GPIO17` | Motor direction |
| `IN2` | Raspberry Pi `GPIO27` | Motor direction |
| `ENA` | Raspberry Pi `GPIO18` | Motor speed with PWM |
| `OUT1` | Motor wire 1 | Motor output |
| `OUT2` | Motor wire 2 | Motor output |
| `GND` | Raspberry Pi `GND` | Shared logic ground |
| `GND` | External power supply `-` | Motor power return |
| `+12V` / `VMS` / motor input | External power supply `+` | Motor power input |

## If You Disable The L298N 5V Jumper

If the `5V_EN` jumper is removed or disabled, also connect:

| L298N Pin | Connect To |
| --- | --- |
| `5V` | External regulated `5V +` |
| `GND` | External regulated `5V -` |

Do not power the motor from the Raspberry Pi 5V pin.

## Diagram

```text
Raspberry Pi GPIO17 ---- L298N IN1
Raspberry Pi GPIO27 ---- L298N IN2
Raspberry Pi GPIO18 ---- L298N ENA

Raspberry Pi GND ------- L298N GND
Power supply - --------- L298N GND
Power supply + --------- L298N +12V / VMS / motor input

L298N OUT1 ------------- Motor wire 1
L298N OUT2 ------------- Motor wire 2
```

## Install Python Libraries

```bash
python3 -m pip install gpiozero lgpio
```

## Run The One Motor Test

From this folder:

```bash
python3 l298n_one_motor.py
```

From the project root:

```bash
python3 py/l298n_one_motor.py
```

## Expected Behavior

The motor should:

1. Spin forward for 2 seconds.
2. Stop for 1 second.
3. Spin backward for 2 seconds.
4. Stop.

If the direction is reversed, swap the two motor wires on `OUT1` and `OUT2`.
