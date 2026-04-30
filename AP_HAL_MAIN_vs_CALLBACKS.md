# AP_HAL_MAIN vs AP_HAL_MAIN_CALLBACKS

Both macros are defined in:

- `ardupilot/libraries/AP_HAL/AP_HAL_Main.h`

## Definitions

`AP_HAL_MAIN()` is defined at `AP_HAL_Main.h:25`.

It creates an `AP_HAL::HAL::FunCallbacks` object from global `setup()` and
`loop()` functions, then passes that callback object into `hal.run()`:

```cpp
#define AP_HAL_MAIN() \
    AP_HAL::HAL::FunCallbacks callbacks(setup, loop); \
    extern "C" {                               \
    int AP_MAIN(int argc, char* const argv[]); \
    int AP_MAIN(int argc, char* const argv[]) { \
        hal.run(argc, argv, &callbacks); \
        return 0; \
    } \
    }
```

`AP_HAL_MAIN_CALLBACKS(CALLBACKS)` is defined at `AP_HAL_Main.h:35`.

It directly passes an existing callback object into `hal.run()`:

```cpp
#define AP_HAL_MAIN_CALLBACKS(CALLBACKS) extern "C" { \
    int AP_MAIN(int argc, char* const argv[]); \
    int AP_MAIN(int argc, char* const argv[]) { \
        hal.run(argc, argv, CALLBACKS); \
        return 0; \
    } \
    }
```

## Difference

`AP_HAL_MAIN()` is used by examples and sketches that provide plain global
`setup()` and `loop()` functions.

`AP_HAL_MAIN_CALLBACKS(...)` is used by full vehicle applications. The vehicle
object itself is passed as the callback provider.

## Example Call Sites

Rover:

```cpp
Rover rover;
AP_Vehicle& vehicle = rover;

AP_HAL_MAIN_CALLBACKS(&rover);
```

Source:

- `ardupilot/Rover/Rover.cpp:560`

Copter:

```cpp
Copter copter;
AP_Vehicle& vehicle = copter;

AP_HAL_MAIN_CALLBACKS(&copter);
```

Source:

- `ardupilot/ArduCopter/Copter.cpp:995`

Examples using `AP_HAL_MAIN()` include:

- `ardupilot/libraries/AP_HAL/examples/RCOutput/RCOutput.cpp`
- `ardupilot/libraries/AP_HAL/examples/AnalogIn/AnalogIn.cpp`
- `ardupilot/libraries/AP_AHRS/examples/AHRS_Test/AHRS_Test.cpp`

## Entry Point

Both macros generate the program entry point:

```cpp
int main(int argc, char* const argv[])
```

Technically the generated function name is `AP_MAIN`. If `AP_MAIN` is not
already defined, `AP_HAL_Main.h` defines it as `main`:

```cpp
#ifndef AP_MAIN
#define AP_MAIN main
#endif
```
