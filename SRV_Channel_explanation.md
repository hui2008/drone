# SRV_Channel Code Explanation

## Short Answer

`duff/libraries/SRV_Channel` is not frontend code. It is embedded firmware actuator-output code. It maps high-level vehicle outputs like throttle, motor1, aileron, lights, sprayer, camera trigger, and user actuators onto physical output channels, then converts those logical outputs into PWM, DShot, CAN, or servo-protocol writes through `hal.rcout`.

## Main Pieces

`SRV_Channel` represents one physical output channel: `SERVO1`, `SERVO2`, etc.

Source: `duff/libraries/SRV_Channel/SRV_Channel.h`

It owns that channel's output parameters:

- `MIN`
- `MAX`
- `TRIM`
- `REVERSED`
- `FUNCTION`

These parameters are declared in `duff/libraries/SRV_Channel/SRV_Channel.cpp`.

`FUNCTION` is the important mapping. It tells the firmware what the physical output does. The enum includes values like:

- `k_motor1`
- `k_throttle`
- `k_aileron`
- `k_steering`
- `k_lights1`
- `k_actuator1`
- `k_sprayer_pump`
- `k_cam_trigger`

`SRV_Channels` manages the whole array of `SRV_Channel` objects. It is the API most other code calls.

Source: `duff/libraries/SRV_Channel/SRV_Channel.h`

## How Data Flows

1. Vehicle code writes a logical output.

   Example:

   ```cpp
   SRV_Channels::set_output_scaled(SRV_Channel::k_throttle, value);
   SRV_Channels::set_output_pwm(SRV_Channel::k_sprayer_spinner, pwm);
   ```

2. `SRV_Channels` stores that value by function, not directly by physical channel.

   The function-to-channel mapping is built in:

   ```text
   duff/libraries/SRV_Channel/SRV_Channel_aux.cpp
   SRV_Channels::update_aux_servo_function()
   ```

3. Each function gets an output type.

   `SRV_Channel::aux_servo_function_setup()` decides whether a function is:

   - angle-style, such as `-4500..4500`
   - range-style, such as `0..100` or `0..1000`

4. `SRV_Channels::calc_pwm()` converts scaled logical values into physical PWM.

   It loops through all configured channels and calls each channel's `SRV_Channel::calc_pwm()`.

5. `SRV_Channel::calc_pwm()` applies:

   - `SERVOx_MIN`
   - `SERVOx_MAX`
   - `SERVOx_TRIM`
   - `SERVOx_REVERSED`
   - emergency stop behavior for dangerous outputs
   - temporary override behavior

6. Conversion happens through:

   ```text
   SRV_Channel::pwm_from_range()
   SRV_Channel::pwm_from_angle()
   ```

7. `SRV_Channels::output_ch_all()` writes final channel outputs.

   It calls `SRV_Channel::output_ch()` for each channel. That function handles special RC passthrough modes, then writes to hardware:

   ```cpp
   hal.rcout->write(ch_num, output_pwm);
   ```

8. `SRV_Channels::push()` flushes the outputs and updates extra output protocols.

   Depending on build options, it updates protocols such as:

   - Volz
   - SBUS output
   - Robotis servo
   - BLHeli telemetry
   - FETtec OneWire
   - KDE CAN
   - DroneCAN
   - PiccoloCAN

## Important Source Files

- `duff/libraries/SRV_Channel/SRV_Channel.h`
  - Defines `SRV_Channel`, `SRV_Channels`, output functions, and public APIs.

- `duff/libraries/SRV_Channel/SRV_Channel.cpp`
  - Defines per-channel parameters and scaled-to-PWM conversion.

- `duff/libraries/SRV_Channel/SRV_Channels.cpp`
  - Defines global channel management, initialization, `calc_pwm()`, `push()`, emergency stop, and protocol forwarding.

- `duff/libraries/SRV_Channel/SRV_Channel_aux.cpp`
  - Defines function-to-channel setup, passthrough behavior, output writing, failsafe helpers, and helpers like `set_output_scaled()`.

- `duff/libraries/SRV_Channel/SRV_Channel_config.h`
  - Defines compile-time configuration such as `NUM_SERVO_CHANNELS`.

## What Components Call It

Vehicle-level code owns a `SRV_Channels servo_channels` object in its parameter structure.

Examples:

- `duff/ArduCopter/Parameters.h`
- `duff/ArduPlane/Parameters.h`
- `duff/Rover/Parameters.h`
- `duff/ArduSub/Parameters.h`
- `duff/Blimp/Parameters.h`
- `duff/AntennaTracker/Tracker.h`
- `duff/Tools/AP_Periph/AP_Periph.h`

The main output loops call `calc_pwm()`, `output_ch_all()`, and `push()`.

Examples:

- `duff/ArduCopter/motors.cpp`
- `duff/ArduPlane/servos.cpp`
- `duff/ArduSub/motors.cpp`
- `duff/Blimp/motors.cpp`
- `duff/Tools/AP_Periph/rc_out.cpp`
- `duff/AntennaTracker/servos.cpp`

Many subsystem libraries call it for specific actuator outputs:

- `duff/libraries/AC_Sprayer`
- `duff/libraries/AP_ICEngine`
- `duff/libraries/RC_Channel`
- `duff/libraries/AP_BLHeli`
- `duff/libraries/AP_DroneCAN`
- `duff/libraries/AP_PiccoloCAN`
- `duff/libraries/AP_Scripting`
- camera, mount, winch, gripper, lights, landing gear, and related actuator modules

## Typical Runtime Pattern

For a vehicle such as Plane or Copter, the pattern is:

```text
flight/control logic
  -> SRV_Channels::set_output_scaled(function, value)
  -> SRV_Channels::calc_pwm()
  -> SRV_Channels::output_ch_all()
  -> AP::srv().push()
  -> hal.rcout / DShot / CAN / servo protocol
  -> physical actuator
```

## Why This Layer Exists

This library separates "what the vehicle wants to do" from "which physical pin or output bus performs it."

For example, Plane code can say:

```cpp
SRV_Channels::set_output_scaled(SRV_Channel::k_aileron, roll_out);
```

It does not need to know whether the aileron is on `SERVO1`, `SERVO5`, a reversed output, a remapped channel, or a CAN actuator. `SRV_Channel` applies the channel configuration and sends the final value to the output backend.

## Frontend?

No. This is backend embedded firmware. More specifically, it is a low-level actuator routing and output abstraction layer used by autopilot vehicle code.

It has no UI rendering, no web app behavior, and no frontend framework. It controls physical outputs.
