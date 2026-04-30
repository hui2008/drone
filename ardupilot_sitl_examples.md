# ArduPilot SITL Example Targets

This list is for `/workspaces/uav/ardupilot` after configuring SITL:

```sh
cd /workspaces/uav/ardupilot
./waf configure --board sitl
./waf list
```

Build one example with a real target name:

```sh
./waf --targets examples/RCOutput
```

## Buildable Examples And Source Paths

| Target | Source directory |
|---|---|
| `examples/AC_PID_test` | `libraries/AC_PID/examples/AC_PID_test` |
| `examples/AHRS_Test` | `libraries/AP_AHRS/examples/AHRS_Test` |
| `examples/AP_Common` | `libraries/AP_Common/examples/AP_Common` |
| `examples/AP_Compass_test` | `libraries/AP_Compass/examples/AP_Compass_test` |
| `examples/AP_Declination_test` | `libraries/AP_Declination/examples/AP_Declination_test` |
| `examples/AP_FW_Controller_test` | `libraries/APM_Control/examples/AP_FW_Controller_test` |
| `examples/AP_Logger_AllTypes` | `libraries/AP_Logger/examples/AP_Logger_AllTypes` |
| `examples/AP_Logger_test` | `libraries/AP_Logger/examples/AP_Logger_test` |
| `examples/AP_Marvelmind_test` | `libraries/AP_Beacon/examples/AP_Marvelmind_test` |
| `examples/AP_Mission_test` | `libraries/AP_Mission/examples/AP_Mission_test` |
| `examples/AP_Motors_test` | `libraries/AP_Motors/examples/AP_Motors_test` |
| `examples/AP_Notify_test` | `libraries/AP_Notify/examples/AP_Notify_test` |
| `examples/AP_OpticalFlow_test` | `libraries/AP_OpticalFlow/examples/AP_OpticalFlow_test` |
| `examples/AP_Parachute_test` | `libraries/AP_Parachute/examples/AP_Parachute_test` |
| `examples/Airspeed` | `libraries/AP_Airspeed/examples/Airspeed` |
| `examples/AnalogIn` | `libraries/AP_HAL/examples/AnalogIn` |
| `examples/BARO_generic` | `libraries/AP_Baro/examples/BARO_generic` |
| `examples/BinarySem` | `libraries/AP_HAL/examples/BinarySem` |
| `examples/CompassCalibrator_index_test` | `libraries/AP_Compass/examples/CompassCalibrator_index_test` |
| `examples/DSP_test` | `libraries/AP_HAL/examples/DSP_test` |
| `examples/Derivative` | `libraries/Filter/examples/Derivative` |
| `examples/File_IO` | `libraries/AP_Filesystem/examples/File_IO` |
| `examples/Filter` | `libraries/Filter/examples/Filter` |
| `examples/FlashTest` | `libraries/AP_FlashStorage/examples/FlashTest` |
| `examples/GPS_AUTO_test` | `libraries/AP_GPS/examples/GPS_AUTO_test` |
| `examples/GPS_UBLOX_passthrough` | `libraries/AP_GPS/examples/GPS_UBLOX_passthrough` |
| `examples/ICM20789` | `libraries/AP_Baro/examples/ICM20789` |
| `examples/INS_generic` | `libraries/AP_InertialSensor/examples/INS_generic` |
| `examples/LowPassFilter` | `libraries/Filter/examples/LowPassFilter` |
| `examples/LowPassFilter2p` | `libraries/Filter/examples/LowPassFilter2p` |
| `examples/ModuleTest` | `libraries/AP_Module/examples/ModuleTest` |
| `examples/NMEA_Output` | `libraries/AP_NMEA_Output/examples/NMEA_Output` |
| `examples/Printf` | `libraries/AP_HAL/examples/Printf` |
| `examples/RCInput` | `libraries/AP_HAL/examples/RCInput` |
| `examples/RCInputToRCOutput` | `libraries/AP_HAL/examples/RCInputToRCOutput` |
| `examples/RCOutput` | `libraries/AP_HAL/examples/RCOutput` |
| `examples/RCOutput2` | `libraries/AP_HAL/examples/RCOutput2` |
| `examples/RCProtocolDecoder` | `libraries/AP_RCProtocol/examples/RCProtocolDecoder` |
| `examples/RCProtocolTest` | `libraries/AP_RCProtocol/examples/RCProtocolTest` |
| `examples/RC_Channel` | `libraries/RC_Channel/examples/RC_Channel` |
| `examples/RC_UART` | `libraries/RC_Channel/examples/RC_UART` |
| `examples/RFIND_test` | `libraries/AP_RangeFinder/examples/RFIND_test` |
| `examples/RNG_test` | `libraries/AP_HAL/examples/RNG_test` |
| `examples/RPM_generic` | `libraries/AP_RPM/examples/RPM_generic` |
| `examples/RTC_test` | `libraries/AP_RTC/examples/RTC_test` |
| `examples/ReplayGyroFFT` | `libraries/AP_GyroFFT/examples/ReplayGyroFFT` |
| `examples/RingBuffer` | `libraries/AP_HAL/examples/RingBuffer` |
| `examples/Scheduler_test` | `libraries/AP_Scheduler/examples/Scheduler_test` |
| `examples/SlewLimiter` | `libraries/Filter/examples/SlewLimiter` |
| `examples/SmartRTL_test` | `libraries/AP_SmartRTL/examples/SmartRTL_test` |
| `examples/Storage` | `libraries/AP_HAL/examples/Storage` |
| `examples/StorageTest` | `libraries/StorageManager/examples/StorageTest` |
| `examples/ToshibaLED_test` | `libraries/AP_Notify/examples/ToshibaLED_test` |
| `examples/TransferFunctionCheck` | `libraries/Filter/examples/TransferFunctionCheck` |
| `examples/UART_chargen` | `libraries/AP_HAL/examples/UART_chargen` |
| `examples/UART_test` | `libraries/AP_HAL/examples/UART_test` |
| `examples/XPlane` | `libraries/AP_JSON/examples/XPlane` |
| `examples/eulers` | `libraries/AP_Math/examples/eulers` |
| `examples/expo_inverse_test` | `libraries/AP_Motors/examples/expo_inverse_test` |
| `examples/jedec_test` | `libraries/AP_FlashIface/examples/jedec_test` |
| `examples/location` | `libraries/AP_Math/examples/location` |
| `examples/matrix_alg` | `libraries/AP_Math/examples/matrix_alg` |
| `examples/onvif_test` | `libraries/AP_ONVIF/examples/onvif_test` |
| `examples/polygon` | `libraries/AP_Math/examples/polygon` |
| `examples/rotations` | `libraries/AP_Math/examples/rotations` |
| `examples/routing` | `libraries/GCS_MAVLink/examples/routing` |

## Source Lookup

To verify a target source path:

```sh
find /workspaces/uav/ardupilot/libraries -path '*/examples/RCOutput'
```
