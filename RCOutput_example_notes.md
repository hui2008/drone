# RCOutput Example Notes

Source:

```text
ardupilot/libraries/AP_HAL/examples/RCOutput/RCOutput.cpp
```

## What It Tests

This is a simple HAL `RCOutput` example. It does not use `SRV_Channel`.

It calls the lower-level HAL output interface directly:

```cpp
hal.rcout->enable_ch(i);
hal.rcout->write(i, pwm);
```

The example enables channels `0..13`, which correspond to:

```text
SERVO1 .. SERVO14
```

## Input

There is no external input.

The example generates its own PWM value:

```cpp
static uint16_t pwm = 1500;
static int8_t delta = 1;
```

Runtime behavior:

```text
pwm starts at 1500
pwm increments by 1 after each channel write
when pwm reaches 2000, direction changes to decreasing
when pwm reaches 1000, direction changes to increasing
loop delay is 5 ms
```

So the output sweeps:

```text
1500 -> 2000 -> 1000 -> 2000 -> ...
```

Console output:

```text
Starting AP_HAL::RCOutput test
decreasing
increasing
decreasing
...
```

## How To Build And Run

From the `ardupilot` directory:

```bash
./waf configure --board sitl
./waf --targets examples/RCOutput
./build/sitl/examples/RCOutput
```

For hardware:

```bash
./waf configure --board <your_board>
./waf --targets examples/RCOutput --upload
```

On hardware, connect a servo, ESC, or oscilloscope to outputs `SERVO1..SERVO14`. If the board has a safety switch, press it; otherwise PWM output may remain disabled.

## SITL Behavior

In SITL this does not generate real PWM.

The call path reaches the SITL HAL implementation:

```text
hal.rcout
  -> HALSITL::RCOutput
  -> libraries/AP_HAL_SITL/RCOutput.cpp
```

SITL `RCOutput::write()` stores PWM values in simulated output state instead of driving hardware pins.

## Meaningful Preprocessed Code For SITL

For `--board sitl`, the ChibiOS-only block is removed because:

```text
CONFIG_HAL_BOARD = HAL_BOARD_SITL
```

Original ChibiOS-only block:

```cpp
#if CONFIG_HAL_BOARD == HAL_BOARD_CHIBIOS
#include <AP_BoardConfig/AP_BoardConfig.h>
#include <AP_IOMCU/AP_IOMCU.h>
AP_BoardConfig BoardConfig;
#endif
```

That block is not present in the SITL preprocessed path.

The meaningful preprocessed shape is:

```cpp
#include <AP_HAL/AP_HAL.h>

void setup();
void loop();

const AP_HAL::HAL& hal = AP_HAL::get_HAL();

void setup(void)
{
    hal.console->printf("Starting AP_HAL::RCOutput test\n");

    for (uint8_t i = 0; i < 14; i++) {
        hal.rcout->enable_ch(i);
    }
}

static uint16_t pwm = 1500;
static int8_t delta = 1;

void loop(void)
{
    for (uint8_t i = 0; i < 14; i++) {
        hal.rcout->write(i, pwm);
        pwm += delta;

        if (delta > 0 && pwm >= 2000) {
            delta = -1;
            hal.console->printf("decreasing\n");
        } else if (delta < 0 && pwm <= 1000) {
            delta = 1;
            hal.console->printf("increasing\n");
        }
    }

    hal.scheduler->delay(5);
}

AP_HAL::HAL::FunCallbacks callbacks(setup, loop);

extern "C" {
int main(int argc, char* const argv[]);
int main(int argc, char* const argv[])
{
    hal.run(argc, argv, &callbacks);
    return 0;
}
}
```

`AP_HAL_MAIN();` expands from:

```text
ardupilot/libraries/AP_HAL/AP_HAL_Main.h
```

Expansion:

```cpp
AP_HAL::HAL::FunCallbacks callbacks(setup, loop);

extern "C" {
int AP_MAIN(int argc, char* const argv[]);
int AP_MAIN(int argc, char* const argv[])
{
    hal.run(argc, argv, &callbacks);
    return 0;
}
}
```

For normal builds, `AP_MAIN` defaults to `main`.

## Current Local Build Note

I configured SITL successfully:

```bash
./waf configure --board sitl
```

Building the example was blocked before compile by a missing Python dependency:

```text
you need to install empy with 'python3 -m pip install empy==3.3.4'
```

Because of that, I did not generate a full compiler `-E` preprocessed output file. The full `-E` output would be much larger than the source because it expands all included headers.
