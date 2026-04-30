# ArduPilot HAL, Frontend, and Backend Notes

## Short answer

In ArduPilot drivers, the HAL is used by both the frontend and backend, but it is used most heavily by the backend.

The typical layering is:

```text
Vehicle / AHRS / control code
    |
Driver frontend
    |
Driver backend
    |
AP_HAL
    |
Board / OS / MCU / bus hardware
```

## Inertial sensor example

For the IMU/inertial sensor library:

- Frontend class: `AP_InertialSensor`
- Frontend interface file: `ardupilot/libraries/AP_InertialSensor/AP_InertialSensor.h`
- Backend base class: `AP_InertialSensor_Backend`
- Backend interface file: `ardupilot/libraries/AP_InertialSensor/AP_InertialSensor_Backend.h`

There is no class named `AP_InertialSensor_Frontend`. The frontend is simply the main class, `AP_InertialSensor`.

The backend stores a reference to the frontend, but in this library it is named `_imu`, not `_frontend`:

```cpp
AP_InertialSensor &_imu;
```

Other ArduPilot libraries may use clearer names such as `_frontend`, for example barometer backends.

## Where HAL is called

### Frontend use of HAL

The frontend uses HAL mainly for discovery and construction of backend drivers.

For example, `AP_InertialSensor.cpp` gets bus device handles from HAL:

```cpp
hal.spi->get_device(...)
hal.i2c_mgr->get_device(...)
```

It then passes those HAL device objects into backend probe functions, such as:

```cpp
AP_InertialSensor_BMI270::probe(*this, hal.spi->get_device(...), rotation)
```

So the frontend is responsible for deciding which backend drivers to try and giving them access to the right HAL bus/device object.

### Backend use of HAL

The backend uses HAL for the actual hardware communication and timing.

Concrete backends store an `AP_HAL::Device`, `AP_HAL::SPIDevice`, `AP_HAL::I2CDevice`, or serial port object and use it to talk to the hardware:

```cpp
_dev->read_registers(...)
_dev->write_register(...)
_dev->transfer(...)
_dev->register_periodic_callback(...)
```

Backends may also call global HAL services directly:

```cpp
hal.scheduler->delay(...)
hal.scheduler->delay_microseconds(...)
hal.console->printf(...)
```

## Key distinction

The frontend/backend split is an ArduPilot driver architecture pattern:

- frontend: public API, parameters, calibration, health, instance management, common logic
- backend: specific sensor/protocol/device implementation

The HAL is a lower-level portability layer:

- SPI
- I2C
- UART
- GPIO
- scheduler/timing
- RC input/output
- storage
- CAN
- board/OS-specific services

So HAL is not only "about the board". It is also the abstraction that lets a backend driver communicate with hardware without knowing whether it is running on ChibiOS, SITL, Linux, or another platform.

## Practical rule

If vehicle code wants IMU data, it should call the frontend:

```cpp
ins.get_gyro()
ins.get_accel()
ins.get_gyro_health()
ins.get_accel_health()
```

If a backend wants to read a chip register or schedule sensor polling, it uses HAL:

```cpp
_dev->read_registers(...)
hal.scheduler->delay(...)
```

The vehicle code should not normally talk to HAL directly to access the IMU.

