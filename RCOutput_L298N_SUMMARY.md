## RCOutput_L298N — L298N Motor Driver for ArduPilot (Duffy Board)

### Overview
`RCOutput_L298N` is a Linux RC output driver for the L298N dual H-bridge motor controller, targeting the "Duffy" board (Raspberry Pi-based rover). It implements the `AP_HAL::RCOutput` interface, supporting 2 motors with forward/reverse control and PWM speed regulation.

### GPIO Assignments

| Function | GPIO | Pi Pin | Type |
|---|---|---|---|
| Motor A IN1 (forward) | 17 | 11 | Digital output |
| Motor A IN2 (reverse) | 27 | 13 | Digital output |
| Motor A speed (ENA) | 18 | 12 | Hardware PWM0 |
| Motor B IN1 (forward) | 22 | 15 | Digital output |
| Motor B IN2 (reverse) | 23 | 16 | Digital output |
| Motor B speed (ENB) | 13 | 33 | Hardware PWM1 |

Pin assignments are compile-time constants defined in `hwdef/duffy/hwdef.dat`.

### Key Design Details
- **Deadband:** PWM values 1490–1510 µs are treated as stop (no motor movement)
- **Direction:** Values above 1510 µs = forward, below 1490 µs = reverse
- **Speed:** Magnitude scales linearly from 0–100% over the 1500–2000 µs (forward) or 1000–1500 µs (reverse) range
- **Cork/Push:** Buffered output — `cork()` batches writes, `push()` applies them simultaneously to both motors

### Avoiding GPIO Conflicts
- Both hardware PWM channels (PWM0, PWM1) are used — no other PWM available without external hardware
- Disable `dtparam=audio=on` in `/boot/config.txt` (audio conflicts with PWM0/PWM1)
- I2C (GPIO 2, 3), SPI (GPIO 7–11), and UART (GPIO 14, 15) are safe — no overlap
- Available GPIOs for other peripherals: 4, 5, 6, 12, 16, 19, 20, 21, 24, 25, 26

### Files
- **Header:** `libraries/AP_HAL_Linux/RCOutput_L298N.h`
- **Implementation:** `libraries/AP_HAL_Linux/RCOutput_L298N.cpp`
- **Pin definitions:** `libraries/AP_HAL_Linux/hwdef/duffy/hwdef.dat`
- **Board registration:** `libraries/AP_HAL_Linux/HAL_Linux_Class.cpp`
