# SITL Board Targets

This note summarizes the SITL-related board targets reported by:

```sh
./waf list_boards
```

## Vehicle SITL targets

| Board | Purpose | Main difference |
| --- | --- | --- |
| `sitl` | Normal desktop SITL build | Uses the native host toolchain by default. This is the standard target for local vehicle simulation. |
| `SITL_x86_64_linux_gnu` | Portable x86-64 Linux SITL | Includes the base `sitl` hwdef, forces the `x86_64-linux-gnu` toolchain, and enables static linking. |
| `SITL_arm_linux_gnueabihf` | Portable ARM Linux SITL | Includes the base `sitl` hwdef, forces the `arm-linux-gnueabihf` toolchain, and enables static linking. |

The base `sitl` hwdef is in:

```text
libraries/AP_HAL_SITL/hwdef/sitl/hwdef.dat
```

The architecture-specific targets are in:

```text
libraries/AP_HAL_SITL/hwdef/SITL_x86_64_linux_gnu/hwdef.dat
libraries/AP_HAL_SITL/hwdef/SITL_arm_linux_gnueabihf/hwdef.dat
```

## SITL AP_Periph targets

| Board | Purpose | Main difference |
| --- | --- | --- |
| `sitl_periph_universal` | Simulated AP_Periph with many features | Enables GPS, airspeed, compass, baro, IMU, rangefinder, battery, EFI, RPM, RC out, ADS-B, terrain, ESC telemetry, and related serial options. |
| `sitl_periph_battmon` | Simulated CAN battery monitor | Enables AP_Periph battery support on top of the common periph base. |
| `sitl_periph_battery_tag` | Simulated CAN battery tag | Enables battery tag and RTC/global time support, and disables some unrelated optional features. |
| `sitl_periph_gps` | Simulated CAN GPS peripheral | Enables AP_Periph GPS support on top of the common periph base. |
| `sitl_periph_can_to_serial` | Simulated CAN serial passthrough peripheral | Uses the serial passthrough CAN app node name. No extra sensor feature is enabled in its hwdef. |

All `sitl_periph_*` targets include the common AP_Periph SITL base:

```text
libraries/AP_HAL_SITL/hwdef/sitl_periph/hwdef.inc
```

That shared base sets `AP_PERIPH=1`, `HAL_BUILD_AP_PERIPH=1`, and disables most peripheral features by default. Each specific `sitl_periph_*` board then opts in only the features it needs.

## HAL run implementation

The `run()` method declared in `AP_HAL::HAL` is a pure virtual backend entry point:

```text
libraries/AP_HAL/HAL.h
```

Each HAL backend implements it. The SITL implementation is:

```text
libraries/AP_HAL_SITL/HAL_SITL_Class.cpp
```

For `--board sitl`, `HAL_SITL::run()` is the implementation used. It initializes the SITL utility layer, SITL state, scheduler, serial port 0, RC input, RC output, and analog input. It then calls `callbacks->setup()`, marks the scheduler initialized, and enters the main loop.

The SITL main loop repeatedly:

- exits if the SITL scheduler asks to stop
- calls `callbacks->loop()`
- runs SITL IO processing
- updates watchdog persistence when the watchdog is enabled

Other HAL backends also implement the same interface:

| Backend | Implementation file |
| --- | --- |
| SITL | `libraries/AP_HAL_SITL/HAL_SITL_Class.cpp` |
| ChibiOS | `libraries/AP_HAL_ChibiOS/HAL_ChibiOS_Class.cpp` |
| Linux | `libraries/AP_HAL_Linux/HAL_Linux_Class.cpp` |
| ESP32 | `libraries/AP_HAL_ESP32/HAL_ESP32_Class.cpp` |
| QURT | `libraries/AP_HAL_QURT/HAL_QURT_Class.cpp` |
| Empty HAL | `libraries/AP_HAL_Empty/HAL_Empty_Class.cpp` |

## RCOutput support

The `sitl` target has an `RCOutput` HAL implementation.

SITL creates a `HALSITL::RCOutput` object and passes it into the HAL as `hal.rcout`:

```text
libraries/AP_HAL_SITL/HAL_SITL_Class.cpp
```

The implementation is in:

```text
libraries/AP_HAL_SITL/RCOutput.h
libraries/AP_HAL_SITL/RCOutput.cpp
```

This is simulated output, not hardware PWM. `RCOutput::write()` stores PWM values in the SITL state `pwm_output` array. SITL supports 32 output channels through `SITL_NUM_CHANNELS`, defined in:

```text
libraries/SITL/SITL.h
```

The SITL implementation also includes safety handling, `cork()`/`push()` batching, and simulated ESC telemetry update support.

## Common usage

For normal vehicle simulation:

```sh
./waf configure --board sitl
```

For DroneCAN/AP_Periph simulation and tests, use the relevant `sitl_periph_*` board. Autotest uses `sitl_periph_universal` for CAN tests and `sitl_periph_battmon` for battery CAN tests.
