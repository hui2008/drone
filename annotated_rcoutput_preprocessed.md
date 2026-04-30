# Annotated Preprocessed `RCOutput.cpp`

Source used:

- [RCOutput.cpp.source_only.readable.ii](/workspaces/uav/ardupilot/build/sitl/libraries/AP_HAL/examples/RCOutput/RCOutput.cpp.source_only.readable.ii)

## Annotated Listing

```cpp
void setup();
void loop();
```

- Forward declarations for the two callback functions used by the HAL entrypoint.
- These appear before the callback object is constructed.

```cpp
const AP_HAL::HAL& hal = AP_HAL::get_HAL();
```

- Gets the global HAL singleton for the current board configuration.
- Under `sitl`, this resolves to the SITL HAL implementation.
- The rest of the example uses this object to access console, RC output, and scheduler services.

```cpp
void setup (void)
{
    hal.console->printf("Starting AP_HAL::RCOutput test\n");

    for (uint8_t i = 0; i< 14; i++) {
        hal.rcout->enable_ch(i);
    }
}
```

- `setup()` is the one-time initialization callback.
- It prints a startup message to the HAL console.
- Then it enables RC output channels `0` through `13`.
- `hal.rcout` is the HAL RC output driver abstraction.

```cpp
static uint16_t pwm = 1500;
static int8_t delta = 1;
```

- Persistent state used by `loop()`.
- `pwm` starts at `1500` microseconds, roughly the middle of a typical servo range.
- `delta` controls whether the test output is currently increasing or decreasing.

```cpp
void loop (void)
{
    for (uint8_t i=0; i < 14; i++) {
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
```

- `loop()` is the recurring callback executed by the HAL runtime.
- For each RC output channel:
  - write the current PWM value
  - step `pwm` by `delta`
  - reverse direction at the endpoints
- The endpoints are `1000` and `2000` microseconds, a common servo test range.
- When the sweep reverses direction, it prints `"decreasing"` or `"increasing"` to the console.
- `hal.scheduler->delay(5)` pauses for 5 ms before the next iteration.

```cpp
AP_HAL::HAL::FunCallbacks callbacks(setup, loop);
```

- This packages the two function pointers into the callback type expected by the HAL runtime.
- It is part of the `AP_HAL_MAIN()` expansion.

```cpp
extern "C" {
int main(int argc, char* const argv[]);
int main(int argc, char* const argv[]) {
    hal.run(argc, argv, &callbacks);
    return 0;
}
}
```

- This is the key macro expansion that was hidden in the original source.
- `AP_HAL_MAIN()` expands into a normal C entrypoint.
- `extern "C"` gives `main` C linkage.
- `hal.run(...)` transfers control to the HAL runtime, which:
  - initializes the platform
  - calls `setup()` once
  - repeatedly calls `loop()`

## Summary

The original example is small, but preprocessing makes one important hidden step explicit:

- `AP_HAL_MAIN()` becomes a real `main(...)`
- that `main(...)` hands control to `hal.run(...)`
- the HAL runtime then drives `setup()` and `loop()`
