# SRV_Channel Code Explanation

## Short Answer

`ardupilot/libraries/SRV_Channel` maps high-level vehicle outputs like throttle, motor1, aileron, lights, sprayer, camera trigger, and user actuators onto physical output channels, then converts those logical outputs into PWM, DShot, CAN, or servo-protocol writes through `hal.rcout`.

## Main Pieces

`SRV_Channel` represents one physical output channel: `SERVO1`, `SERVO2`, etc.

Source: `ardupilot/libraries/SRV_Channel/SRV_Channel.h`

It owns that channel's output parameters:

- `MIN`
- `MAX`
- `TRIM`
- `REVERSED`
- `FUNCTION`

These parameters are declared in `ardupilot/libraries/SRV_Channel/SRV_Channel.cpp`.

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

Source: `ardupilot/libraries/SRV_Channel/SRV_Channel.h`

## How Many Channels

ArduPilot supports up to 32 SRV output channels:

```text
SERVO1 .. SERVO32
```

In code, channel constants are zero-indexed:

```text
ardupilot/libraries/AP_HAL/RCOutput.h
CH_1  = 0
CH_2  = 1
...
CH_32 = 31
```

The compile-time count is controlled by `NUM_SERVO_CHANNELS`:

```text
ardupilot/libraries/SRV_Channel/SRV_Channel_config.h

#if HAL_PROGRAM_SIZE_LIMIT_KB > 1024
    NUM_SERVO_CHANNELS = 32
#else
    NUM_SERVO_CHANNELS = 16
#endif
```

So the library has:

- 32 channels on larger firmware targets
- 16 channels on smaller firmware targets
- actual physical output availability depends on the board and HAL backend

There is also a runtime parameter gate for the upper channels:

```text
SERVO_32_ENABLE
```

When `NUM_SERVO_CHANNELS >= 17`, outputs above `SERVO16` are parameterized as `SERVO17` through `SERVO32`, but they are disabled by default through `SERVO_32_ENABLE = 0`.

The constructor also defaults channels above 16 to GPIO:

```text
ardupilot/libraries/SRV_Channel/SRV_Channels.cpp
SRV_Channels::SRV_Channels()
  -> if channel index >= 16
       SERVOx_FUNCTION default = k_GPIO
```

## What Each Channel Does

A channel does whatever its `SERVOx_FUNCTION` parameter says. There is no universal rule that `SERVO1` always means one specific actuator across all vehicles.

Each channel has these parameters:

```text
SERVOx_MIN
SERVOx_MAX
SERVOx_TRIM
SERVOx_REVERSED
SERVOx_FUNCTION
```

`SERVOx_FUNCTION` is the role assignment. Default from `SRV_Channel` itself is:

```text
ardupilot/libraries/SRV_Channel/SRV_Channel.cpp
SERVOx_FUNCTION = 0 = Disabled
```

Some common function values:

```text
-1   GPIO
0    Disabled
1    RC passthrough
4    Aileron
19   Elevator
21   Rudder
22   SprayerPump
23   SprayerSpinner
26   GroundSteering
28   Gripper
29   LandingGear
33   Motor1
34   Motor2
35   Motor3
36   Motor4
70   Throttle
71   TrackerYaw
72   TrackerPitch
73   ThrottleLeft
74   ThrottleRight
88   Winch
94   Script1
95   Script2
...
109  Script16
120  NeoPixel1
121  NeoPixel2
122  NeoPixel3
123  NeoPixel4
140  RCIN1Scaled
...
155  RCIN16Scaled
180  CameraZoom
181  Lights1
182  Lights2
183  VideoSwitch
184  Actuator1
...
189  Actuator6
```

Vehicle code sets some defaults:

| Vehicle | Default channel functions |
| --- | --- |
| Plane | `SERVO1=Aileron`, `SERVO2=Elevator`, `SERVO3=Throttle`, `SERVO4=Rudder` |
| Rover | `SERVO1=GroundSteering`, `SERVO3=Throttle` |
| AntennaTracker | `SERVO1=TrackerYaw`, `SERVO2=TrackerPitch` |
| AP_Periph | `SERVO1..N=RCIN1..N`, up to `HAL_PWM_COUNT` |
| Copter/Sub/Blimp | Usually configured by the frame/motor library, not by a single fixed SRV table |

Examples:

```text
ardupilot/ArduPlane/Parameters.cpp
SERVO1 -> k_aileron
SERVO2 -> k_elevator
SERVO3 -> k_throttle
SERVO4 -> k_rudder

ardupilot/Rover/Parameters.cpp
SERVO1 -> k_steering
SERVO3 -> k_throttle

ardupilot/AntennaTracker/servos.cpp
SERVO1 -> k_tracker_yaw
SERVO2 -> k_tracker_pitch

ardupilot/Tools/AP_Periph/rc_out.cpp
SERVO1..N -> k_rcin1..k_rcinN
```

Motor-frame code often assigns motor functions dynamically:

```text
ardupilot/libraries/AP_Motors/AP_Motors_Class.cpp
AP_Motors::add_motor_num(motor_num)
  -> SRV_Channels::get_motor_function(motor_num)
  -> SRV_Channels::set_aux_channel_default(function, motor_num)
```

`get_motor_function()` maps zero-based motor indexes to motor functions:

```text
0  -> k_motor1
1  -> k_motor2
...
7  -> k_motor8
8  -> k_motor9
...
11 -> k_motor12
12 -> k_motor13
...
31 -> k_motor32
```

That is why Copter/Sub motor channel meaning depends on `FRAME_CLASS`, `FRAME_TYPE`, and the motor layout code in `AP_Motors`.

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
   ardupilot/libraries/SRV_Channel/SRV_Channel_aux.cpp
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

- `ardupilot/libraries/SRV_Channel/SRV_Channel.h`
  - Defines `SRV_Channel`, `SRV_Channels`, output functions, and public APIs.

- `ardupilot/libraries/SRV_Channel/SRV_Channel.cpp`
  - Defines per-channel parameters and scaled-to-PWM conversion.

- `ardupilot/libraries/SRV_Channel/SRV_Channels.cpp`
  - Defines global channel management, initialization, `calc_pwm()`, `push()`, emergency stop, and protocol forwarding.

- `ardupilot/libraries/SRV_Channel/SRV_Channel_aux.cpp`
  - Defines function-to-channel setup, passthrough behavior, output writing, failsafe helpers, and helpers like `set_output_scaled()`.

- `ardupilot/libraries/SRV_Channel/SRV_Channel_config.h`
  - Defines compile-time configuration such as `NUM_SERVO_CHANNELS`.

## What Components Call It

Most code does not call individual `SRV_Channel` objects directly. It calls the manager, `SRV_Channels`, usually through static helpers such as `SRV_Channels::set_output_scaled()` or through the singleton accessor `AP::srv()`.

Vehicle-level code owns a `SRV_Channels servo_channels` object in its parameter structure. The `SRV_Channels` constructor installs that object as the singleton:

```text
ardupilot/libraries/SRV_Channel/SRV_Channels.cpp
SRV_Channels::SRV_Channels()
  -> _singleton = this
  -> channels = obj_channels

ardupilot/libraries/SRV_Channel/SRV_Channels.cpp
AP::srv()
  -> *SRV_Channels::get_singleton()
```

Examples:

- `ardupilot/ArduCopter/Parameters.h`
- `ardupilot/ArduPlane/Parameters.h`
- `ardupilot/Rover/Parameters.h`
- `ardupilot/ArduSub/Parameters.h`
- `ardupilot/Blimp/Parameters.h`
- `ardupilot/AntennaTracker/Tracker.h`
- `ardupilot/Tools/AP_Periph/AP_Periph.h`

The main output loops call `calc_pwm()`, `output_ch_all()`, and `push()`.

Examples:

- `ardupilot/ArduCopter/motors.cpp`
- `ardupilot/ArduPlane/servos.cpp`
- `ardupilot/ArduSub/motors.cpp`
- `ardupilot/Blimp/motors.cpp`
- `ardupilot/Tools/AP_Periph/rc_out.cpp`
- `ardupilot/AntennaTracker/servos.cpp`
- `ardupilot/libraries/AR_Motors/AP_MotorsUGV.cpp`

Many subsystem libraries call it for specific actuator outputs:

- `ardupilot/libraries/AC_Sprayer`
- `ardupilot/libraries/AP_ICEngine`
- `ardupilot/libraries/AP_Parachute`
- `ardupilot/libraries/AP_Winch`
- `ardupilot/libraries/AP_Gripper`
- `ardupilot/libraries/AP_Camera`
- `ardupilot/libraries/AP_LandingGear`
- `ardupilot/libraries/AP_Generator`
- `ardupilot/libraries/AP_Motors`
- `ardupilot/libraries/AR_Motors`
- `ardupilot/libraries/AP_Notify`
- camera, mount, winch, gripper, lights, landing gear, and related actuator modules

## Who Calls It, When, And How

### Startup and Configuration

At vehicle startup, generic vehicle initialization calls:

```text
ardupilot/libraries/AP_Vehicle/AP_Vehicle.cpp
AP::srv().init()
```

Vehicle-specific startup or radio setup then calls:

```text
AP::srv().enable_aux_servos()
```

Examples include:

- `ardupilot/ArduCopter/radio.cpp`
- `ardupilot/ArduCopter/Copter.cpp`
- `ardupilot/ArduPlane/Plane.cpp`
- `ardupilot/ArduPlane/radio.cpp`
- `ardupilot/Rover/system.cpp`
- `ardupilot/Rover/Rover.cpp`
- `ardupilot/ArduSub/Sub.cpp`
- `ardupilot/Blimp/Blimp.cpp`
- `ardupilot/Blimp/radio.cpp`
- `ardupilot/AntennaTracker/servos.cpp`
- `ardupilot/Tools/AP_Periph/rc_out.cpp`

`enable_aux_servos()` is important because it calls:

```text
SRV_Channels::update_aux_servo_function()
```

That function reads each `SERVOx_FUNCTION`, calls `SRV_Channel::aux_servo_function_setup()`, builds the function-to-channel masks, and enables or disables physical output channels through `hal.rcout`.

### Control Code Writes Logical Outputs

During flight or vehicle operation, controllers and actuator libraries write logical outputs by function:

```cpp
SRV_Channels::set_output_scaled(SRV_Channel::k_aileron, roll_out);
SRV_Channels::set_output_scaled(SRV_Channel::k_throttle, throttle);
SRV_Channels::set_output_pwm(SRV_Channel::k_gripper, pwm);
SRV_Channels::set_output_limit(SRV_Channel::k_landing_gear_control, SRV_Channel::Limit::MAX);
```

`set_output_scaled()` stores the value in:

```text
functions[function].output_scaled
```

It does not immediately write hardware. It also clears the direct-PWM mask for every channel assigned to that function, so the next `calc_pwm()` can regenerate PWM from the scaled value.

`set_output_pwm()` is different: it sets PWM directly on all channels assigned to the function and calls `SRV_Channel::output_ch()` immediately.

### Main Output Loops Flush The Values

The main vehicle output loops are where stored logical outputs become physical outputs.

Copter pattern:

```text
ardupilot/ArduCopter/motors.cpp
Copter::motors_output()
  -> SRV_Channels::calc_pwm()
  -> AP::srv().cork()
  -> SRV_Channels::output_ch_all()
  -> flightmode->output_to_motors()
  -> AP::srv().push() or hal.rcout->push()
```

Plane pattern:

```text
ardupilot/ArduPlane/servos.cpp
Plane::servos_output()
  -> AP::srv().cork()
  -> servos_twin_engine_mix()
  -> channel_function_mixer()
  -> tailsitter / tiltrotor / spoiler / landing updates
  -> SRV_Channels::calc_pwm()
  -> SRV_Channels::output_ch_all()
  -> AP::srv().push()
```

Sub pattern:

```text
ardupilot/ArduSub/motors.cpp
Sub motor output path
  -> AP::srv().cork()
  -> SRV_Channels::calc_pwm()
  -> SRV_Channels::output_ch_all()
  -> motors.output()
  -> AP::srv().push()
```

Blimp pattern:

```text
ardupilot/Blimp/motors.cpp
Blimp::motors_output()
  -> SRV_Channels::calc_pwm()
  -> AP::srv().cork()
  -> SRV_Channels::output_ch_all()
  -> motors->output()
  -> AP::srv().push()
```

Rover uses the UGV motor library:

```text
ardupilot/libraries/AR_Motors/AP_MotorsUGV.cpp
AP_MotorsUGV::output()
  -> AP::srv().cork()
  -> SRV_Channels::calc_pwm()
  -> SRV_Channels::output_ch_all()
  -> AP::srv().push()
```

AP_Periph updates only when new actuator data has arrived:

```text
ardupilot/Tools/AP_Periph/rc_out.cpp
AP_Periph_FW::rcout_update()
  -> SRV_Channels::calc_pwm()
  -> AP::srv().cork()
  -> SRV_Channels::output_ch_all()
  -> AP::srv().push()
```

### Internal Per-Channel Calls

`SRV_Channels::calc_pwm()` loops over every configured channel:

```text
SRV_Channels::calc_pwm()
  -> channels[i].calc_pwm(functions[channels[i].function].output_scaled)
```

`SRV_Channel::calc_pwm()` applies direct-PWM override behavior, emergency-stop behavior, temporary overrides, and scaled-to-PWM conversion.

`SRV_Channels::output_ch_all()` loops over physical channels:

```text
SRV_Channels::output_ch_all()
  -> channels[i].output_ch()
```

`SRV_Channel::output_ch()` handles special RC passthrough functions such as `k_manual`, `k_rcin1..k_rcin16`, and mapped RC input functions. Then it writes the channel:

```cpp
hal.rcout->write(ch_num, output_pwm);
```

`AP::srv().cork()` and `AP::srv().push()` are wrappers around `hal.rcout->cork()` and `hal.rcout->push()`. `push()` also updates optional output protocols such as SBUS, Volz, Robotis, BLHeli telemetry, FETtec OneWire, KDE CAN, DroneCAN, and PiccoloCAN when those features are compiled in.

## Code Called By SRV_Channel

This section is the downstream direction: once vehicle code reaches `SRV_Channel` or `SRV_Channels`, what lower-level code is called next?

### Per-Channel Conversion Calls

`SRV_Channel::calc_pwm()` is mostly a value conversion function.

Source:

```text
ardupilot/libraries/SRV_Channel/SRV_Channel.cpp
SRV_Channel::calc_pwm()
```

Call path:

```text
SRV_Channel::calc_pwm(output_scaled)
  -> SRV_Channel::should_e_stop(function)
  -> SRV_Channel::pwm_from_scaled_value(output_scaled)
       -> SRV_Channel::pwm_from_angle(...)
       or SRV_Channel::pwm_from_range(...)
```

These helpers do not call hardware. They use channel state and parameters:

- `SERVOx_MIN`
- `SERVOx_MAX`
- `SERVOx_TRIM`
- `SERVOx_REVERSED`
- `high_out`
- `type_angle`
- direct-PWM override state
- temporary override state
- emergency-stop state

### Per-Channel Output Calls

`SRV_Channel::output_ch()` is the direct hardware-facing method.

Source:

```text
ardupilot/libraries/SRV_Channel/SRV_Channel_aux.cpp
SRV_Channel::output_ch()
```

For normal functions, the path is short:

```text
SRV_Channel::output_ch()
  -> hal.rcout->write(ch_num, output_pwm)
```

For RC passthrough functions, it reads RC input first:

```text
SRV_Channel::output_ch()
  -> rc().channel(...)
  -> RC_Channel::get_radio_in()
  -> RC_Channel::get_radio_trim()
  -> RC_Channel::norm_input_dz()
  -> RC_Channel::norm_input_ignore_trim()
  -> rc().has_valid_input()
  -> rc().in_rc_failsafe()
  -> SRV_Channel::pwm_from_angle(...)
  -> SRV_Channel::pwm_from_range(...)
  -> hal.rcout->write(ch_num, output_pwm)
```

The RC-input branch is used for functions such as:

- `k_manual`
- `k_rcin1` through `k_rcin16`
- `k_rcin1_mapped` through `k_rcin16_mapped`

### Manager Calls Into Channels

`SRV_Channels` is the manager layer that calls each `SRV_Channel`.

Source:

```text
ardupilot/libraries/SRV_Channel/SRV_Channels.cpp
SRV_Channels::calc_pwm()
```

Call path:

```text
SRV_Channels::calc_pwm()
  -> channels[i].set_override(...)
  -> channels[i].calc_pwm(functions[channels[i].function].output_scaled)
```

Source:

```text
ardupilot/libraries/SRV_Channel/SRV_Channel_aux.cpp
SRV_Channels::output_ch_all()
```

Call path:

```text
SRV_Channels::output_ch_all()
  -> channels[i].output_ch()
```

`SRV_Channels` also calls per-channel helpers when setting direct values:

```text
SRV_Channels::set_output_pwm(...)
  -> channels[i].set_output_pwm(...)
  -> channels[i].output_ch()

SRV_Channels::set_output_limit(...)
  -> channels[i].get_limit_pwm(...)
  -> channels[i].set_output_pwm(...)
```

### HAL RCOutput Calls

`SRV_Channel` and `SRV_Channels` stop at the HAL output abstraction. The actual board, SITL, Linux, PWM, DShot, or serial implementation is behind `hal.rcout`.

Important calls:

```text
hal.rcout->write(ch_num, output_pwm)
hal.rcout->cork()
hal.rcout->push()
hal.rcout->enable_ch(ch_num)
hal.rcout->disable_ch(ch_num)
hal.rcout->set_default_rate(...)
hal.rcout->set_freq(mask, frequency_hz)
hal.rcout->set_failsafe_pwm(mask, pwm)
hal.rcout->set_esc_scaling(min_pwm, max_pwm)
hal.rcout->set_dshot_rate(rate, loop_rate_hz)
hal.rcout->update_channel_masks()
```

This is the boundary where `SRV_Channel` stops knowing about the concrete output hardware.

### Protocol And CAN Calls After Push

`SRV_Channels::push()` first flushes the HAL RC output buffer:

```text
SRV_Channels::push()
  -> hal.rcout->push()
```

Then, depending on compile-time options, it updates other output backends:

```text
SRV_Channels::push()
  -> volz.update()
  -> sbus.update()
  -> robotis.update()
  -> blheli.update_telemetry()
  -> fetteconwire.update()
  -> AP::kdecan()->update()
  -> AP::can().get_num_drivers()
  -> AP::can().get_driver_type(...)
  -> AP_DroneCAN::get_dronecan(...)
  -> AP_DroneCAN::SRV_push_servos()
  -> AP_PiccoloCAN::get_pcan(...)
  -> AP_PiccoloCAN::update()
```

So the downstream shape is:

```text
SRV_Channels
  -> SRV_Channel
      -> RC_Channel, only for RC passthrough/mapped RC output
      -> AP_Math helpers such as constrain_float()
      -> hal.rcout
          -> board-specific RCOutput backend
          -> PWM / DShot / serial ESC / CAN output protocols
```

## Typical Runtime Pattern

For a vehicle such as Plane or Copter, the pattern is:

```text
flight/control logic
  -> SRV_Channels::set_output_scaled(function, value)
  -> AP::srv().cork()
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

No. This is backend embedded firmware. More specifically, it is a low-level actuator routing and output abstraction layer used by autopilot vehicle code. It controls physical outputs.
