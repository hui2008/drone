# AP_HAL_Empty File Guide

`ardupilot/libraries/AP_HAL_Empty` is ArduPilot's stub or "empty" Hardware Abstraction Layer (HAL). It provides concrete classes that satisfy the `AP_HAL` interfaces without talking to real hardware. Most methods are no-ops, return fixed defaults, or store minimal in-memory state. This makes the directory useful as a skeleton for new HAL ports and as a build target where hardware behavior is intentionally absent.

## Top-Level Structure

The module is organized around one exported HAL class, `HAL_Empty`, plus stub implementations for serial, GPIO, analog input, storage, RC input/output, scheduler, bus devices, flash, optical flow, DSP, and semaphores.

The public entry point is `AP_HAL_Empty.h`. Internal implementation files include `AP_HAL_Empty_Private.h`, which pulls in the concrete driver headers used by `HAL_Empty_Class.cpp`.

## Files

| File | Purpose |
| --- | --- |
| `AP_HAL_Empty.h` | Umbrella public header for the Empty HAL. It includes `AP_HAL/AP_HAL.h` and exports `HAL_Empty_Class.h`. The comments explain the expected pattern for HAL modules: expose only the `AP_HAL::HAL` implementation publicly, keep implementation details under the `Empty` namespace, and guard compilation with `CONFIG_HAL_BOARD == HAL_BOARD_EMPTY`. |
| `AP_HAL_Empty_Namespace.h` | Forward-declares every class implemented by the Empty HAL inside the `Empty` namespace. This lets headers refer to `Empty::GPIO`, `Empty::UARTDriver`, and the other driver types without needing all full definitions immediately. |
| `AP_HAL_Empty_Private.h` | Private umbrella header for the Empty HAL implementation. It includes the concrete driver headers such as `AnalogIn.h`, `GPIO.h`, `RCInput.h`, `Scheduler.h`, `SPIDevice.h`, `Storage.h`, `UARTDriver.h`, `Flash.h`, and `DSP.h`. It should only be included from inside `AP_HAL_Empty`. |
| `HAL_Empty_Class.h` | Declares `HAL_Empty`, the concrete class derived from `AP_HAL::HAL`. It exposes the constructor and overrides `run()`, which is the main HAL execution entry point. |
| `HAL_Empty_Class.cpp` | Instantiates the Empty HAL's singleton-style driver objects, wires them into the `AP_HAL::HAL` base constructor, implements `HAL_Empty::run()`, and defines `AP_HAL::get_HAL()` plus `AP_HAL::get_HAL_mutable()`. The run loop initializes the scheduler, starts serial 0 at 115200 baud, calls setup, marks the system initialized, and then calls the user loop forever. It only compiles when `CONFIG_HAL_BOARD == HAL_BOARD_EMPTY`. |
| `AnalogIn.h` | Declares `Empty::AnalogSource` and `Empty::AnalogIn`. `AnalogSource` implements the analog source interface, while `AnalogIn` provides HAL-level access to analog channels and board voltage. |
| `AnalogIn.cpp` | Implements fixed analog behavior. `AnalogSource` stores a float sample value, returns it for average/latest reads, and converts it to a 0-5 V scale with a 1024-count divisor. `AnalogIn::channel()` allocates a new `AnalogSource` with value `1.11`, and `board_voltage()` always returns `5.0f`. |
| `DSP.h` | Declares a stub `Empty::DSP` implementation when `HAL_WITH_DSP` is enabled. FFT methods return `nullptr` or `0`, and vector math methods either do nothing or return `0.0f`. In `HAL_Empty_Class.cpp`, the HAL currently passes `nullptr` for DSP, so this class is available but not wired into the Empty HAL instance there. |
| `Flash.h` | Defines a stub `Empty::Flash` class. Page address, page size, and page count return `0`; erase, write, and page-erased checks return `false`; `keep_unlocked()` is a no-op. This satisfies the flash interface without persistent or writable flash behavior. |
| `GPIO.h` | Declares `Empty::GPIO` and `Empty::DigitalSource`. `GPIO` implements pin mode, read/write/toggle, channel creation, and USB connection status. `DigitalSource` is the alternate per-pin interface with local state. |
| `GPIO.cpp` | Implements GPIO as a no-op hardware layer. Direct GPIO reads always return `0`, writes and toggles do nothing, and `usb_connected()` returns `false`. `GPIO::channel()` allocates a `DigitalSource` initialized to `0`; that object stores written values and toggles its internal byte state. |
| `I2CDevice.h` | Defines `Empty::I2CDevice` and `Empty::I2CDeviceManager`. The device accepts address/retry changes as no-ops, reports successful transfers and speed changes, returns `nullptr` for its semaphore, and returns `nullptr` for registered callbacks. The manager's `get_device_ptr()` returns `nullptr`, so no actual I2C device is provided by default. |
| `OpticalFlow.h` | Declares a stub optical flow driver. `init()` does nothing, `read()` returns `false` to indicate no frame was produced, and gyro input methods are no-ops. |
| `RCInput.h` | Declares the Empty RC input driver. It implements initialization, input availability, channel count, single-channel reads, bulk reads, and reports its protocol string as `"Empty"`. |
| `RCInput.cpp` | Implements deterministic fake RC input. `new_input()` is always `false`, `num_channels()` is `0`, channel 2 reads as `900` microseconds for low throttle safety, and all other channels read as `1500` microseconds. Bulk reads fill the caller's buffer using the same values. |
| `RCOutput.h` | Declares the Empty RC output driver. It implements frequency configuration, channel enable/disable, write/read methods, and no-op `cork()`/`push()` batching hooks. It stores up to 16 output values in a local array. |
| `RCOutput.cpp` | Implements in-memory RC output state. Frequency is fixed at `50` Hz, enable/disable and frequency setting are no-ops, valid channel writes update the `value[16]` array, valid reads return the stored value, invalid reads return `900`, and bulk reads copy stored values up to the array size. |
| `Scheduler.h` | Defines a stub scheduler. Timing delays, timer process registration, IO process registration, failsafe registration, and initialization are no-ops. `is_system_initialized()` always returns `true`, `set_system_initialized()` does nothing, and `reboot()` enters an infinite loop. |
| `Semaphores.h` | Declares `Empty::Semaphore`, a minimal AP_HAL semaphore implementation with `give()`, blocking `take()`, nonblocking `take_nonblocking()`, and `check_owner()`. It stores a private `_taken` flag. |
| `Semaphores.cpp` | Implements the semaphore as a simple boolean lock. `take()` delegates to `take_nonblocking()`, `take_nonblocking()` succeeds only when `_taken` is false, and `give()` succeeds only when `_taken` is true. The comments note that this does not use real synchronization primitives. |
| `SPIDevice.h` | Defines `Empty::SPIDevice` and `Empty::SPIDeviceManager`. SPI transfers and speed changes return success without moving real data. Each SPI device owns an `Empty::Semaphore` returned by `get_semaphore()`. The manager allocates and returns a new `SPIDevice` for a requested device name. |
| `Storage.h` | Declares the Empty nonvolatile storage driver with initialization, block read, and block write methods. |
| `Storage.cpp` | Implements storage as nonpersistent empty memory. `init()` and `write_block()` do nothing. `read_block()` fills the destination buffer with zeroes, so all stored data appears erased or unset. |
| `UARTDriver.h` | Declares the Empty UART driver. It implements the AP_HAL UART and stream methods for begin/end/flush, availability, input discard, read, write, transmit space, initialization state, transmit pending state, and optional UART stats reporting. |
| `UARTDriver.cpp` | Implements serial behavior as a sink/source stub. Begin/end/flush are no-ops, `is_initialized()` and `tx_pending()` return `false`, `_available()` returns `0`, `txspace()` returns `1`, `_write()` reports that all bytes were accepted, and `_read()` returns `0` bytes. When UART stats are enabled, it prints `EMPTY`. |
| `Util.h` | Defines `Empty::Util` as an empty subclass of `AP_HAL::Util`. It relies on the base interface defaults and adds no Empty-specific utility behavior. |
| `WSPIDevice.h` | Defines stub wide-SPI support. `Empty::WSPIDevice::transfer()` returns `false`, command header updates are ignored, and `get_semaphore()` returns `nullptr`. `Empty::WSPIDeviceManager` derives from `AP_HAL::WSPIDeviceManager` without adding behavior. The file also defines `HAL_USE_WSPI_DEFAULT_CFG` to `1` if it was not already set. |

## Behavior Summary

- Most drivers are placeholders, not hardware implementations.
- Serial writes pretend to succeed, while serial reads produce no data.
- Storage reads return zero-filled data, and storage writes are ignored.
- RC input returns safe fixed values, with throttle channel 2 held low at `900`.
- RC output stores values in memory but does not drive hardware.
- GPIO direct reads return low, while `DigitalSource` objects keep local state.
- I2C and SPI transfer methods mostly report success, but I2C device lookup returns no device and SPI lookup allocates a stub device.
- The scheduler does not actually schedule timed or IO callbacks.
- The HAL run method still follows the standard ArduPilot setup/loop structure.

