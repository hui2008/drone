# Rover, Callbacks, AP_Scheduler, and ChibiOS::Scheduler

Generated on 2026-05-03.

This document explains how Rover starts on the ChibiOS HAL, how the callback object reaches the ChibiOS runtime, why ArduPilot uses the `setup()` / `loop()` lifecycle, and how the vehicle scheduler (`AP_Scheduler`) differs from the ChibiOS platform scheduler (`ChibiOS::Scheduler`).

## Table of Contents

| Section | Contents |
| --- | --- |
| [1. Big Picture](#1-big-picture) | High-level Rover to HAL to scheduler flow. |
| [2. Runtime Call Chain](#2-runtime-call-chain) | End-to-end runtime call path on ChibiOS. |
| [3. Execution Lifecycle: setup() / loop()](#3-execution-lifecycle-setup--loop) | Why ArduPilot keeps the common lifecycle pattern. |
| [4. Callback Dispatch and Implementations](#4-callback-dispatch-and-implementations) | Callback interface, HAL main macros, implementations, and Rover's callback object. |
| [5. Scheduler Ownership and Execution](#5-scheduler-ownership-and-execution) | Vehicle scheduler vs platform scheduler, ChibiOS initialization, loop locations, and comparison. |
| [6. Rover Task Table](#6-rover-task-table) | `Rover::scheduler_tasks[]` and the numbered task list. |
| [7. Startup and Setup Functions](#7-startup-and-setup-functions) | Common `AP_Vehicle::setup()`, Rover `init_ardupilot()`, and scheduler hooks. |
| [8. Sensor Setup and Update Tasks](#8-sensor-setup-and-update-tasks) | Sensor initialization path and periodic sensor update tasks. |
| [9. Mermaid Class Diagram](#9-mermaid-class-diagram) | Class and ownership relations with file paths. |
| [10. Summary](#10-summary) | Condensed summary of the document. |
| [Appendix A. Source File Map](#appendix-a-source-file-map) | Relevant files and core terms. |
| [Appendix B. Abbreviations](#appendix-b-abbreviations) | Alphabetical abbreviation glossary. |

## 1. Big Picture

`Rover.cpp` does not directly include or call `AP_HAL_ChibiOS/Scheduler.cpp`.

The code path is indirect:

```text
Rover application object
  defines global Rover rover
  passes &rover to AP_HAL_MAIN_CALLBACKS()

Generated entry point
  AP_HAL_MAIN_CALLBACKS(&rover)
  generates main()
  calls hal.run(argc, argv, &rover)

ChibiOS HAL object ownership
  hal is AP_HAL::get_HAL()
  AP_HAL::get_HAL() returns global HAL_ChibiOS hal_chibios
  HAL_ChibiOS owns ChibiOS::Scheduler schedulerInstance
  HAL_ChibiOS passes &schedulerInstance into AP_HAL::HAL
  AP_HAL::HAL stores it as hal.scheduler

ChibiOS HAL runtime
  HAL_ChibiOS::run()
  stores callbacks in g_callbacks
  enters main_loop()
  starts ChibiOS::Scheduler through hal.scheduler
  calls g_callbacks->setup()
  repeatedly calls g_callbacks->loop()

Rover callback dispatch
  g_callbacks == &rover
  Rover inherits AP_Vehicle
  AP_Vehicle implements AP_HAL::HAL::Callbacks
  g_callbacks->loop() calls AP_Vehicle::loop()

Vehicle scheduler dispatch
  AP_Vehicle::loop()
  calls AP_Scheduler::loop()
  AP_Scheduler runs Rover::scheduler_tasks[]

Vehicle scheduler ownership
  AP_Vehicle has an AP_Scheduler scheduler member
  AP_Scheduler constructor sets the AP_Scheduler singleton
  AP::scheduler() returns that same scheduler object
```

The key distinction:

```text
ChibiOS::Scheduler does not schedule Rover::scheduler_tasks[].
AP_Scheduler schedules Rover::scheduler_tasks[].
ChibiOS::Scheduler provides HAL/platform timing, ChibiOS threads, delays,
timer callbacks, IO callbacks, RC input/output service threads, storage
service, watchdog handling, and priority control.
```

## 2. Runtime Call Chain

```text
Rover.cpp
  AP_HAL_MAIN_CALLBACKS(&rover)
    -> generated main()
      -> hal.run(argc, argv, &rover)
         where callbacks == &rover
        -> HAL_ChibiOS::run(...)
          -> g_callbacks = callbacks
          -> main_loop()
            -> chThdSetPriority(APM_MAIN_PRIORITY)
            -> optional I2C bus clear
            -> optional shared DMA init
            -> peripheral_power_enable()
            -> hal.serial(0)->begin(...)
            -> hal.analogin->init()
            -> hal.scheduler->init()
               -> ChibiOS::Scheduler::init()
               -> starts monitor/timer/rcout/rcin/io/storage platform threads
            -> hal_chibios_set_priority(APM_STARTUP_PRIORITY)
            -> schedulerInstance.hal_initialized()
            -> g_callbacks->setup()
               -> AP_Vehicle::setup() on the rover object
               -> AP::scheduler().init(...)
                  initializes AP_Vehicle::scheduler
               -> Rover-specific init through virtual hooks
            -> schedulerInstance.watchdog_pat()
            -> hal.scheduler->set_system_initialized()
               -> ChibiOS::Scheduler::set_system_initialized()
            -> chThdSetPriority(APM_MAIN_PRIORITY)
            -> loop forever:
                 g_callbacks->loop()
                   -> AP_Vehicle::loop() on the rover object
                     -> AP_Scheduler::loop()
                       -> AP_Scheduler::run(time_available)
                         -> tasks from Rover::scheduler_tasks[]
                 -> optional hal.scheduler->delay_microseconds(50)
                 -> schedulerInstance.watchdog_pat()
```

The platform-specific outer loop is in `libraries/AP_HAL_ChibiOS/HAL_ChibiOS_Class.cpp`, inside `main_loop()`. Rover's vehicle task loop is in `libraries/AP_Vehicle/AP_Vehicle.cpp`, inside `AP_Vehicle::loop()`.

## 3. Execution Lifecycle: setup() / loop()

ArduPilot keeps an Arduino-style lifecycle:

```text
setup()
  initialize once

loop()
  run repeatedly
```

The pattern is kept because ArduPilot runs on very different platforms:

| Platform | Platform runtime concerns |
| --- | --- |
| ChibiOS | RTOS startup, board drivers, hardware definitions, priorities, watchdogs, embedded service threads, interrupt-safe timing. |
| Linux | Process arguments, signal handling, pthreads, UART device paths, CPU affinity, and Linux scheduling. |
| SITL | Simulator timing, simulated devices, and host process integration. |
| Examples/tests | Small programs that only need simple free `setup()` and `loop()` functions. |

The lifecycle separation is:

```text
HAL::run()
  owns platform mechanics and the outer run loop

callbacks->setup()
callbacks->loop()
  own application or vehicle behavior
```

This is inversion of control: the HAL owns platform startup, then calls back into the vehicle or example. Rover does not need ChibiOS-, Linux-, or SITL-specific startup code in its main loop.

For full vehicles, `AP_Vehicle` keeps the lifecycle consistent:

```text
AP_Vehicle::setup()
  common vehicle initialization
  parameter loading
  scheduler initialization
  vehicle-specific initialization through hooks

AP_Vehicle::loop()
  common repeated vehicle loop
  calls AP_Scheduler::loop()
  runs the vehicle task table
```

`AP_Vehicle::loop()` is `final`, so Rover, Plane, Copter, Sub, Blimp, and Tracker do not each invent a different main loop. Vehicle-specific behavior is added through task tables and virtual hooks.

## 4. Callback Dispatch and Implementations

The callback path has three pieces:

| Piece | Role |
| --- | --- |
| `AP_HAL::HAL::Callbacks` | The interface with `setup()` and `loop()`. |
| HAL main macro | Generates the program entry point and passes a callback object to `hal.run(...)`. |
| Runtime callback object | The actual object received by `HAL_ChibiOS::run(...)`; for Rover this is `&rover`. |

### Callback Interface

`AP_HAL::HAL::Callbacks` is defined in `libraries/AP_HAL/HAL.h`:

```cpp
struct Callbacks {
    virtual void setup() = 0;
    virtual void loop() = 0;
};
```

`HAL_ChibiOS::run()` receives a pointer to this interface:

```cpp
void HAL_ChibiOS::run(int argc, char * const argv[], Callbacks* callbacks) const
```

The HAL can therefore run any object that implements `setup()` and `loop()`, without knowing whether it is Rover, another vehicle, an example, or a tool.

### HAL Main Macros

Both macros are defined in `libraries/AP_HAL/AP_HAL_Main.h`.

Both generate the program entry point. The generated function name is `AP_MAIN`; if the build has not defined `AP_MAIN`, the header maps it to normal `main`:

```cpp
#ifndef AP_MAIN
#define AP_MAIN main
#endif
```

### AP_HAL_MAIN()

Use this when the program provides free functions:

```cpp
void setup() {}
void loop() {}

AP_HAL_MAIN();
```

The macro creates a callback wrapper:

```cpp
AP_HAL::HAL::FunCallbacks callbacks(setup, loop);
```

`FunCallbacks` implements `AP_HAL::HAL::Callbacks` by calling those two free functions.

### AP_HAL_MAIN_CALLBACKS()

Use this when the program already has an object that implements the callback interface:

```cpp
Rover rover;
AP_HAL_MAIN_CALLBACKS(&rover);
```

The macro generates `main()` and passes that object directly:

```cpp
hal.run(argc, argv, CALLBACKS);
```

For Rover:

```text
CALLBACKS == &rover
```

### Who Implements AP_HAL::HAL::Callbacks?

The real implementations are:

| Implementation | Where | Used by |
| --- | --- | --- |
| `AP_HAL::HAL::FunCallbacks` | `libraries/AP_HAL/HAL.h` and `libraries/AP_HAL/HAL.cpp` | Example sketches and small programs using `AP_HAL_MAIN()`. |
| `AP_Vehicle` | `libraries/AP_Vehicle/AP_Vehicle.h` and `libraries/AP_Vehicle/AP_Vehicle.cpp` | Full vehicle applications using `AP_HAL_MAIN_CALLBACKS(&vehicle_object)`. |

For Rover, the callback object is the global `rover` object in `Rover.cpp`.

```text
Rover
  inherits AP_Vehicle

AP_Vehicle
  implements AP_HAL::HAL::Callbacks
  provides setup()
  provides loop()
```

`Rover.cpp` has no `Rover::loop()` because Rover uses the inherited final loop from `AP_Vehicle`.

## 5. Scheduler Ownership and Execution

There are two schedulers in this flow, and they solve different problems.

| Scheduler | Layer | Owns | Does not own |
| --- | --- | --- | --- |
| `ChibiOS::Scheduler` | HAL/platform layer | ChibiOS threads, timers, delay services, IO callbacks, timer callbacks, RC input/output service threads, storage service, watchdog, priority management. | Rover's task table. |
| `AP_Scheduler` | Vehicle/application layer | Vehicle task table, task rates, task priorities, loop timing, performance accounting. | ChibiOS platform threads. |

### How the ChibiOS HAL Scheduler Is Initialized

`HAL_ChibiOS` creates one static platform scheduler:

```cpp
static ChibiOS::Scheduler schedulerInstance;
```

The `HAL_ChibiOS` constructor passes it to the base HAL:

```cpp
AP_HAL::HAL(..., &schedulerInstance, ...)
```

The base `AP_HAL::HAL` stores it as:

```cpp
hal.scheduler
```

During `main_loop()`, ChibiOS starts the platform scheduler:

```cpp
hal.scheduler->init();
```

Because `hal.scheduler` points to `schedulerInstance`, this dispatches to:

```text
ChibiOS::Scheduler::init()
```

`ChibiOS::Scheduler::init()` creates platform service threads:

| Thread | Purpose |
| --- | --- |
| monitor | Detect main-loop stalls, save watchdog state, check memory/stack conditions. |
| timer | Runs registered timer processes around 1 kHz and services analog input timer ticks. |
| rcout | Services RC output timing when enabled. |
| rcin | Services RC input timer ticks when enabled. |
| io | Runs registered IO callbacks and periodic low-priority IO work. |
| storage | Processes storage timer ticks and pending storage writes. |

After `g_callbacks->setup()` finishes, `main_loop()` calls:

```cpp
hal.scheduler->set_system_initialized();
```

That marks the ChibiOS platform scheduler as initialized. Some service threads wait for `_hal_initialized`; some monitor behavior waits for `_initialized`.

### How Rover Gets AP_Scheduler

`AP_Vehicle` owns the vehicle scheduler:

```cpp
AP_Scheduler scheduler;
```

The `AP_Scheduler` constructor sets the singleton pointer used by the `AP::scheduler()` accessor. That means:

```text
AP::scheduler()
  returns the AP_Scheduler object owned by the global Rover/AP_Vehicle object
```

During `AP_Vehicle::setup()`:

```cpp
get_scheduler_tasks(tasks, task_count, log_bit);
AP::scheduler().init(tasks, task_count, log_bit);
```

Because `Rover` overrides `get_scheduler_tasks(...)`, the tasks passed to `AP_Scheduler` are:

```text
Rover::scheduler_tasks[]
```

During `AP_Vehicle::loop()`:

```text
AP_Scheduler::loop()
  chooses due tasks
  runs functions from Rover::scheduler_tasks[]
```

### Where Is the Schedule Loop?

There are two relevant loops:

| Loop | File | Function | Meaning |
| --- | --- | --- | --- |
| Platform outer loop | `libraries/AP_HAL_ChibiOS/HAL_ChibiOS_Class.cpp` | `main_loop()` | Forever calls `g_callbacks->loop()`, yields briefly when needed, and pats the watchdog. |
| Vehicle task loop | `libraries/AP_Vehicle/AP_Vehicle.cpp` | `AP_Vehicle::loop()` | Calls `AP_Scheduler::loop()`, which runs due vehicle tasks. |

So the repeated runtime chain is:

```text
ChibiOS main_loop()
  -> g_callbacks->loop()
    -> AP_Vehicle::loop()
      -> AP_Scheduler::loop()
        -> Rover task table entries
```

### Platform Scheduler Loop vs Rover Task Table Loop

| Question | ChibiOS platform scheduler | Rover task table scheduler |
| --- | --- | --- |
| Class | `ChibiOS::Scheduler` | `AP_Scheduler` |
| File | `libraries/AP_HAL_ChibiOS/Scheduler.cpp` | `libraries/AP_Scheduler/AP_Scheduler.cpp` |
| Layer | HAL/platform | Vehicle/application |
| Main responsibility | Make platform services available. | Run vehicle tasks at requested rates. |
| Thread model | Uses ChibiOS threads. | Runs mainly from the vehicle main loop. |
| Runs `Rover::scheduler_tasks[]`? | No. | Yes. |
| Example work | Timer callbacks, IO callbacks, RC input/output service, storage writes, watchdog. | `read_radio`, `ahrs_update`, `set_servos`, GPS update, barometer update, logging, failsafes. |

The short version:

```text
ChibiOS::Scheduler schedules platform service work.
AP_Scheduler schedules Rover's vehicle task table.
```

## 6. Rover Task Table

`Rover::scheduler_tasks[]` is defined in `Rover/Rover.cpp`.

Each row defines:

| Field | Meaning |
| --- | --- |
| Function or class method | The task to run. |
| Hz | Desired run rate. |
| us | Expected runtime budget in microseconds. |
| Priority | Scheduler priority value; lower values are higher priority. |

Numbered Rover task list:

| # | Task | Hz | Budget us | Priority | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | `read_radio` | 50 | 200 | 3 | Reads pilot RC input. |
| 2 | `ahrs_update` | 400 | 400 | 6 | Updates attitude/heading state from inertial and navigation data. |
| 3 | `read_rangefinders` | 50 | 200 | 9 | Enabled when rangefinders are compiled in. |
| 4 | `AP_OpticalFlow::update` | 200 | 160 | 11 | Enabled when optical flow is compiled in. |
| 5 | `update_current_mode` | 400 | 200 | 12 | Runs the active Rover mode update. |
| 6 | `set_servos` | 400 | 200 | 15 | Sends steering/throttle outputs to actuator logic. |
| 7 | `AP_GPS::update` | 50 | 300 | 18 | Updates GPS data. |
| 8 | `AP_Baro::update` | 10 | 200 | 21 | Updates barometer data. |
| 9 | `AP_Beacon::update` | 50 | 200 | 24 | Enabled when beacon support is compiled in. |
| 10 | `AP_Proximity::update` | 50 | 200 | 27 | Enabled when proximity support is compiled in. |
| 11 | `AP_WindVane::update` | 20 | 100 | 30 | Updates wind vane data. |
| 12 | `update_wheel_encoder` | 50 | 200 | 36 | Updates wheel encoder data. |
| 13 | `update_compass` | 10 | 200 | 39 | Updates compass state. |
| 14 | `update_logging1` | 10 | 200 | 45 | Enabled when logging is compiled in. |
| 15 | `update_logging2` | 10 | 200 | 48 | Enabled when logging is compiled in. |
| 16 | `GCS::update_receive` | 400 | 500 | 51 | Handles inbound GCS/MAVLink traffic. |
| 17 | `GCS::update_send` | 400 | 1000 | 54 | Handles outbound GCS/MAVLink traffic. |
| 18 | `RC_Channels::read_mode_switch` | 7 | 200 | 57 | Reads flight mode switch state. |
| 19 | `RC_Channels::read_aux_all` | 10 | 200 | 60 | Reads auxiliary RC channel options. |
| 20 | `AP_BattMonitor::read` | 10 | 300 | 63 | Updates battery monitor data. |
| 21 | `AP_ServoRelayEvents::update_events` | 50 | 200 | 66 | Enabled when servo/relay events are compiled in. |
| 22 | `update_precland` | 400 | 50 | 70 | Enabled when precision landing is compiled in. |
| 23 | `AP_Mount::update` | 50 | 200 | 75 | Enabled when mount support is compiled in. |
| 24 | `AP_Camera::update` | 50 | 200 | 78 | Enabled when camera support is compiled in. |
| 25 | `gcs_failsafe_check` | 10 | 200 | 81 | Checks GCS failsafe conditions. |
| 26 | `fence_check` | 10 | 200 | 84 | Enabled when fence support is compiled in. |
| 27 | `ekf_check` | 10 | 100 | 87 | Checks EKF health. |
| 28 | `ModeSmartRTL::save_position` | 3 | 200 | 90 | Saves SmartRTL path positions. |
| 29 | `one_second_loop` | 1 | 1500 | 96 | Runs low-rate once-per-second work. |
| 30 | `AC_Sprayer::update` | 3 | 90 | 99 | Enabled when sprayer support is compiled in. |
| 31 | `AP_Logger::periodic_tasks` | 50 | 300 | 108 | Enabled when logging is compiled in. |
| 32 | `AP_InertialSensor::periodic` | 400 | 200 | 111 | Runs INS periodic work. |
| 33 | `AP_Scheduler::update_logging` | 0.1 | 200 | 114 | Logs scheduler performance data. |
| 34 | `AP_Button::update` | 5 | 200 | 117 | Enabled when button support is compiled in. |
| 35 | `crash_check` | 10 | 200 | 123 | Checks crash conditions. |
| 36 | `cruise_learn_update` | 50 | 200 | 126 | Updates cruise learning. |
| 37 | `afs_fs_check` | 10 | 200 | 129 | Enabled when advanced failsafe is compiled in. |

Not every row exists in every firmware build. Compile-time options such as `AP_RANGEFINDER_ENABLED`, `HAL_LOGGING_ENABLED`, and `AP_CAMERA_ENABLED` decide which optional tasks are included.

## 7. Startup and Setup Functions

The major setup path is:

```text
HAL_ChibiOS::run()
  -> main_loop()
    -> platform setup before callbacks
    -> g_callbacks->setup()
      -> AP_Vehicle::setup()
        -> load parameters
        -> get_scheduler_tasks(...)
        -> AP::scheduler().init(...)
        -> common vehicle setup
        -> vehicle-specific init hooks
```

Important startup/setup functions:

| Function | File | Role |
| --- | --- | --- |
| `AP_HAL_MAIN_CALLBACKS(&rover)` | `Rover/Rover.cpp` | Generates the entry point that passes `&rover` to `hal.run(...)`. |
| `HAL_ChibiOS::run(...)` | `libraries/AP_HAL_ChibiOS/HAL_ChibiOS_Class.cpp` | ChibiOS HAL entry after generated `main()` calls `hal.run(...)`. |
| `main_loop()` | `libraries/AP_HAL_ChibiOS/HAL_ChibiOS_Class.cpp` | Performs ChibiOS platform startup, starts the HAL scheduler, calls callbacks, and owns the forever loop. |
| `ChibiOS::Scheduler::init()` | `libraries/AP_HAL_ChibiOS/Scheduler.cpp` | Creates ChibiOS platform service threads. |
| `AP_Vehicle::setup()` | `libraries/AP_Vehicle/AP_Vehicle.cpp` | Performs common vehicle setup and initializes `AP_Scheduler`. |
| `Rover::get_scheduler_tasks(...)` | `Rover/Rover.cpp` | Supplies `Rover::scheduler_tasks[]` to `AP_Scheduler`. |
| `Rover::init_ardupilot()` | `Rover/system.cpp` | Performs Rover-specific initialization. |
| `AP_Vehicle::loop()` | `libraries/AP_Vehicle/AP_Vehicle.cpp` | Runs the repeated vehicle loop. |
| `AP_Scheduler::loop()` | `libraries/AP_Scheduler/AP_Scheduler.cpp` | Selects and runs due vehicle tasks. |

ChibiOS-specific platform setup in `main_loop()` includes:

| Step | Why it happens before Rover's setup |
| --- | --- |
| Set main thread priority | Establishes the RTOS priority for the main vehicle thread. |
| Clear I2C buses when configured | Recovers boards where an I2C device may hold the bus during boot. |
| Initialize shared DMA when enabled | Prepares shared DMA arbitration for embedded peripherals. |
| Enable peripheral power | Powers hardware before drivers and sensors use it. |
| Start serial 0 | Makes console output available early. |
| Initialize analog input | Prepares analog input before higher-level vehicle setup. |
| Start `ChibiOS::Scheduler` | Starts platform service threads required by drivers and timing. |
| Lower startup priority temporarily | Lets sensor read loops and low-priority drivers run during setup. |
| Load watchdog data when needed | Preserves reset diagnostics. |
| Mark HAL initialized | Lets platform service threads start normal work. |

## 8. Sensor Setup and Update Tasks

Sensor initialization is split between common vehicle setup, Rover-specific setup, and periodic scheduler tasks.

At a high level:

```text
ChibiOS platform setup
  powers peripherals
  starts serial/analog/platform scheduler service threads
  makes driver timing and IO services available

AP_Vehicle::setup()
  loads parameters
  initializes common vehicle services
  initializes AP_Scheduler with Rover's task table

Rover::init_ardupilot()
  initializes Rover-specific state and subsystems

AP_Scheduler loop
  periodically calls sensor update tasks
```

Important sensor-related task entries:

| Task | Purpose |
| --- | --- |
| `ahrs_update` | Updates AHRS/EKF-facing vehicle attitude and heading state. |
| `AP_InertialSensor::periodic` | Runs periodic INS work. |
| `AP_GPS::update` | Reads and processes GPS updates. |
| `AP_Baro::update` | Reads and processes barometer updates. |
| `update_compass` | Updates compass state. |
| `read_rangefinders` | Reads rangefinder sensors when enabled. |
| `AP_OpticalFlow::update` | Updates optical flow data when enabled. |
| `AP_Proximity::update` | Updates proximity sensors when enabled. |
| `update_wheel_encoder` | Updates wheel encoder data. |
| `AP_WindVane::update` | Updates wind vane data. |
| `AP_BattMonitor::read` | Reads battery sensor data. |

The setup functions prepare sensors and drivers; the task table keeps them fresh during runtime. On ChibiOS, low-level service work can also happen in platform threads such as timer, IO, storage, RC input, and RC output threads.

## 9. Mermaid Class Diagram

<img class="diagram" src="Rover_to_ChibiOS_Scheduler_diagram.svg" alt="Mermaid class diagram">

## 10. Summary

`Rover.cpp` reaches `AP_HAL_ChibiOS/Scheduler.cpp` through the HAL runtime, not through a direct source-level call.

The main flow is:

```text
AP_HAL_MAIN_CALLBACKS(&rover)
  -> HAL_ChibiOS::run(..., &rover)
    -> main_loop()
      -> hal.scheduler->init()
        -> ChibiOS::Scheduler::init()
      -> g_callbacks->setup()
        -> AP_Vehicle::setup()
          -> AP::scheduler().init(Rover::scheduler_tasks[])
      -> forever g_callbacks->loop()
        -> AP_Vehicle::loop()
          -> AP_Scheduler::loop()
            -> Rover task table
```

The important distinction is:

```text
ChibiOS::Scheduler
  platform scheduler
  starts and manages ChibiOS service threads and platform timing

AP_Scheduler
  vehicle scheduler
  runs Rover::scheduler_tasks[]
```

## Appendix A. Source File Map

| File | Why it matters |
| --- | --- |
| `ardupilot/Rover/Rover.cpp` | Defines global `rover`, `Rover::scheduler_tasks[]`, `Rover::get_scheduler_tasks(...)`, and `AP_HAL_MAIN_CALLBACKS(&rover)`. |
| `ardupilot/Rover/Rover.h` | Declares Rover, its scheduler task table, and scheduler task provider method. |
| `ardupilot/Rover/system.cpp` | Contains Rover-specific initialization such as `Rover::init_ardupilot()`. |
| `ardupilot/libraries/AP_HAL/AP_HAL_Main.h` | Defines `AP_HAL_MAIN()` and `AP_HAL_MAIN_CALLBACKS()`. |
| `ardupilot/libraries/AP_HAL/HAL.h` | Defines `AP_HAL::HAL`, `AP_HAL::HAL::Callbacks`, `FunCallbacks`, and the `hal.scheduler` member. |
| `ardupilot/libraries/AP_HAL/Scheduler.h` | Defines the platform scheduler interface implemented by HAL backends. |
| `ardupilot/libraries/AP_HAL/Scheduler.cpp` | Implements common scheduler helper behavior such as delay callbacks. |
| `ardupilot/libraries/AP_HAL_ChibiOS/HAL_ChibiOS_Class.cpp` | Defines `HAL_ChibiOS`, static HAL drivers, `schedulerInstance`, `HAL_ChibiOS::run()`, `main_loop()`, and `AP_HAL::get_HAL()`. |
| `ardupilot/libraries/AP_HAL_ChibiOS/HAL_ChibiOS_Class.h` | Declares `HAL_ChibiOS`. |
| `ardupilot/libraries/AP_HAL_ChibiOS/Scheduler.cpp` | Implements the ChibiOS platform scheduler and service threads. |
| `ardupilot/libraries/AP_HAL_ChibiOS/Scheduler.h` | Declares `ChibiOS::Scheduler`, thread priorities, and thread stack sizes. |
| `ardupilot/libraries/AP_Vehicle/AP_Vehicle.cpp` | Implements common vehicle `setup()` and `loop()`, including `AP_Scheduler` initialization. |
| `ardupilot/libraries/AP_Vehicle/AP_Vehicle.h` | Declares `AP_Vehicle`, its callback methods, and its owned `AP_Scheduler scheduler` member. |
| `ardupilot/libraries/AP_Scheduler/AP_Scheduler.cpp` | Implements vehicle task scheduling. |
| `ardupilot/libraries/AP_Scheduler/AP_Scheduler.h` | Defines `AP_Scheduler::Task` and the scheduler API. |

## Appendix B. Abbreviations

| Abbreviation | Meaning |
| --- | --- |
| AC | ArduCopter or attitude-control prefix, depending on the local class/module name. |
| ADC | Analog-to-digital converter. |
| AFS | Advanced failsafe. |
| AHRS | Attitude and heading reference system. |
| AP | ArduPilot prefix used by many libraries and singleton accessors. |
| AP_HAL | ArduPilot hardware abstraction layer. |
| APM | ArduPilot Mega legacy prefix still used in constants and build names. |
| CAN | Controller area network. |
| CLI | Command-line interface. |
| CPU | Central processing unit. |
| DMA | Direct memory access. |
| EKF | Extended Kalman filter. |
| FS | Failsafe or filesystem, depending on context. |
| GCS | Ground control station. |
| GPS | Global positioning system. |
| HAL | Hardware abstraction layer. |
| I2C | Inter-integrated circuit serial bus. |
| INS | Inertial navigation system or inertial sensor subsystem, depending on context. |
| IO | Input/output. |
| MCU | Microcontroller unit. |
| MAVLink | Micro air vehicle communication protocol. |
| PM | Performance monitoring. |
| PWM | Pulse-width modulation. |
| RC | Radio control. |
| RCIN | Radio-control input. |
| RCOUT | Radio-control output. |
| RTOS | Real-time operating system. |
| SITL | Software in the loop. |
| SPI | Serial peripheral interface. |
| SRV | Servo/output channel subsystem prefix. |
| UART | Universal asynchronous receiver/transmitter. |
| USB | Universal serial bus. |
