# ArduPilot Frontend and Backend Pattern

In ArduPilot firmware, **frontend** and **backend** usually mean:

- **Frontend**: the stable public API used by vehicle code and other libraries.
- **Backend**: the hardware-specific, protocol-specific, or implementation-specific driver behind that API.

This is common in embedded firmware because the vehicle code should not need to know whether a sensor, actuator, telemetry link, or protocol is implemented by one chip, another chip, SITL, CAN, serial, I2C, SPI, etc.

## Pattern Shape

The frontend usually owns:

- public API
- parameters
- shared state
- instance lists
- scheduling/update flow
- detection and backend selection
- common validation and filtering

The backend usually owns:

- hardware-specific reads and writes
- protocol parsing
- bus/device handling
- driver-specific update logic
- pushing measurements or status back into frontend-owned state

This resembles a mix of:

- template method pattern
- strategy pattern
- callback/driver interface pattern

The frontend controls the high-level lifecycle. The backend implements the specific behavior.

## Examples in ArduPilot

Common examples include:

- `AP_InertialSensor`
  - frontend: `AP_InertialSensor`
  - backend base: `AP_InertialSensor_Backend`
  - implementations: specific IMU drivers

- `AP_RangeFinder`
  - frontend: `AP_RangeFinder`
  - backend base: `AP_RangeFinder_Backend`
  - implementations: different rangefinder sensors and protocols

- `AP_Proximity`
  - frontend: `AP_Proximity`
  - backend base: `AP_Proximity_Backend`
  - implementations: lidar, MAVLink, DroneCAN, SITL, scripting, etc.

- `AP_MSP`
  - frontend: `AP_MSP`
  - backend base: `AP_MSP_Telem_Backend`
  - implementations: generic MSP, DJI, DisplayPort, etc.

- `AP_Networking`
  - frontend: `AP_Networking`
  - backend base: `AP_Networking_Backend`
  - implementations: networking-specific backends such as PPP

## Why ArduPilot Uses This

The frontend/backend split lets vehicle code depend on stable behavior instead of specific devices.

For example, vehicle code can ask the rangefinder frontend for distance without knowing whether the data came from:

- a serial lidar
- an I2C rangefinder
- a DroneCAN sensor
- a MAVLink message
- a SITL simulated sensor

That keeps vehicle logic portable across boards, vehicles, and sensor combinations.

## Relation to `SRV_Channel`

`duff/libraries/SRV_Channel` is an actuator routing and output abstraction layer.

It maps logical output functions such as:

- throttle
- motor outputs
- aileron
- steering
- lights
- sprayer
- camera trigger
- user actuators

onto physical output channels and output protocols.

`SRV_Channel` does not follow the same explicit `Frontend` / `Backend` naming style as many sensor libraries. Instead, it sits above lower-level output mechanisms such as:

- `hal.rcout`
- PWM output
- DShot/BLHeli support
- DroneCAN output
- PiccoloCAN output
- SBUS/Volz/Robotis/FETtec output paths, depending on build options

So `SRV_Channel` is best described as a firmware actuator-output abstraction, while many sensor and protocol libraries are best described as frontend/backend driver frameworks.

## Correct Mental Model

For ArduPilot firmware, a useful model is:

- vehicle code uses stable frontend APIs
- frontends manage shared state and policy
- backends implement hardware/protocol-specific behavior
- actuator/output layers route logical commands to physical outputs
- HAL layers perform board-specific IO
