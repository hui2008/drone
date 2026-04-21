# ArduRover on RPi: startup notes

This note is for a minimal Raspberry Pi experiment where `ardurover` is launched directly on Linux without a real rover attached.

Example command:

```sh
sudo ./ardurover --serial1 udpin:0.0.0.0:14550 -l logs -t terrain -s storage
```

Example startup output:

```text
RPI 4

Init ArduRover V4.8.0-dev (bc474e4c)

Free RAM: 262144
AP_Logger_File: buffer size=204800
No Compass backends available
Baro: no sensors found, skipping calibration
Beginning INS calibration. Do not move vehicle
```

## Short answer

If the goal is just to run `ardurover` on a Raspberry Pi and get a rough sense of it, the startup message below is expected:

```text
Beginning INS calibration. Do not move vehicle
```

This is not evidence that a real rover is attached. It is standard startup behavior.

## What the message means

On Rover startup, the INS/IMU code performs gyro calibration by default. In practice, "Do not move vehicle" means:

- Keep the board still during startup.
- Do not rotate, shake, or vibrate the Pi or attached IMU.
- The code is estimating gyro bias and wants a motionless sensor.

Since there is no real rover in this setup, read it as "do not jiggle the Pi during boot."

This line matters because a moving IMU can produce a poor gyro bias estimate. If startup calibration does not converge cleanly, the process may continue, but later pre-arm checks can still complain that gyros are not calibrated.

## How to interpret the other messages

- `No Compass backends available`
  No compass driver was found. This is normal on a bare Pi.
- `Baro: no sensors found, skipping calibration`
  No barometer driver was found. Also normal on a bare Pi.
- `Beginning INS calibration. Do not move vehicle`
  The INS path is initializing and trying to calibrate the gyros.

None of those lines, by themselves, mean the process is broken.

## What this setup is good for

Running native `ardurover` on Linux/RPi without a full vehicle is still useful for:

- startup validation
- MAVLink port bring-up
- parameter loading and persistence
- log file creation
- checking that Linux-target drivers and storage paths behave sensibly
- connecting a GCS and inspecting heartbeats, params, status text, and pre-arm failures

This is enough to get a feel for process startup, the messaging, the parameter system, and some integration behavior.

## What this setup is not

Without real sensors and actuators, it is not a meaningful rover runtime.

More specifically:

- state estimation may be incomplete or invalid
- arming may fail
- mode behavior may not be representative
- navigation behavior is not useful
- control outputs are not a substitute for a real vehicle or SITL

So the binary can be "alive" without the system being operational as a rover.

## Healthy enough for a bare Pi experiment

For a minimal "does it basically run?" check, these are reasonable signs:

- the process stays up
- MAVLink is reachable on the configured UDP port
- logs are created under the expected log directory
- parameters can be read and written
- startup messages stabilize instead of spamming hard faults
- a GCS can connect and show the vehicle type and status text

If those work, the experiment is useful as a Linux integration smoke test.

## QGroundControl heartbeat check

If you are using QGroundControl, the practical heartbeat check is not just "does the link exist?" but "does QGC continuously receive `HEARTBEAT` and identify the vehicle?"

Use this quick procedure:

1. In QGC, open `Application Settings` -> `Comm Links`.
2. Make sure a UDP link is enabled for port `14550`.
3. Start `ardurover`.
4. In QGC, watch for the vehicle connection in the top bar.
5. Open `Widgets` -> `MAVLink Inspector` and check whether `HEARTBEAT` is arriving continuously.

What to look for:

- QGC should show a connected vehicle rather than an empty link
- the vehicle type should resolve to Rover
- status text should begin appearing
- `HEARTBEAT` should update repeatedly rather than appear once and stop

If QGC does not show the vehicle type, assume it has not received a usable `HEARTBEAT` yet.

## QGroundControl UDP direction

This point is easy to miss.

If you launch Rover like this:

```sh
sudo ./ardurover --serial1 udpin:0.0.0.0:14550 -l logs -t terrain -s storage
```

then ArduPilot is listening for inbound UDP on port `14550`.

QGroundControl also typically listens on UDP `14550`.

That means both sides may be waiting for inbound traffic. In practice, this often produces "QGC is open but no vehicle type appears" because no one is actually sending `HEARTBEAT` packets to QGC.

For QGroundControl, it is usually better to have ArduPilot send outbound UDP to the QGC host:

```sh
sudo ./ardurover --serial1 udpout:<QGC_IP>:14550 -l logs -t terrain -s storage
```

Examples:

- QGC on the same machine: `--serial1 udpout:127.0.0.1:14550`
- QGC on another machine on the LAN: `--serial1 udpout:192.168.1.50:14550`

If `udpout` is configured correctly and QGC still does not show a vehicle, check the `MAVLink Inspector` first. If `HEARTBEAT` is missing there, the problem is transport or stream setup rather than the vehicle-type display itself.

## Signs the setup is missing too much to be meaningful

The setup is too incomplete for anything beyond smoke testing if you see one or more of these:

- no IMU is detected at all
- the process remains stuck in repeated initialization failures
- gyro calibration repeatedly fails or pre-arm reports `Gyros not calibrated`
- no stable heartbeat or MAVLink session appears
- parameters do not persist
- logs are not written

At that point, the process may still run, but the result is not informative as a vehicle test.

## Practical startup advice

For a bare Pi experiment:

- place the Pi on a stable surface before launch
- avoid touching it for a few seconds after startup
- do not over-interpret missing compass or barometer messages
- pay more attention to whether IMU initialization completes and whether MAVLink and logging work

If you intentionally need to start while moving, startup gyro calibration becomes a real limitation rather than just a harmless message.

## Bare Pi sanity checklist

Use this as a small checklist for a minimal native Linux test:

- confirm the `ardurover` process remains running for at least a minute
- confirm UDP `14550` is reachable from a GCS
- confirm a heartbeat appears in the GCS
- confirm status text stops at ordinary startup messages instead of escalating to repeated faults
- confirm a log file is created in `logs`
- confirm parameters can be changed and saved
- confirm restarting the process does not immediately show storage corruption or parameter reset

If most of the checklist passes, the setup is doing something useful even without a rover.

## INS, AHRS, and EKF

These terms are related but they are not the same thing.

- `INS` means `Inertial Navigation System`
- `AHRS` means `Attitude and Heading Reference System`
- `EKF` means `Extended Kalman Filter`

In ArduPilot, they roughly stack like this:

- `INS`
  This is the IMU side. It reads gyroscopes and accelerometers, applies offsets and filtering, and provides the low-level inertial measurements.
- `AHRS`
  This sits above the inertial sensors and estimates orientation. It answers the question "which way is the vehicle pointing?"
- `EKF`
  This is the higher-level state estimator. It fuses IMU data with other sensors such as GPS, compass, and barometer to estimate attitude, position, and velocity.

A useful shorthand is:

- `INS` = raw sensor measurements after calibration and filtering
- `AHRS` = attitude estimate
- `EKF` = full navigation/state estimate

For this Raspberry Pi startup case:

- `INS calibration` is the low-level startup step that is happening first
- `AHRS` depends on usable inertial data
- `EKF` only becomes truly useful once enough healthy sensors are present

So seeing `Beginning INS calibration` does not mean the whole navigation stack is working. It only means the inertial sensor layer is being initialized.

## When SITL is the better tool

If the goal is to understand Rover behavior, missions, modes, navigation, or arming logic without real hardware, SITL is the better path.

Use native `ardurover` on RPi when you care about:

- Linux target startup
- runtime integration on the Pi
- serial and UDP interfaces
- file storage and logs
- attached real hardware

Use SITL when you care about:

- vehicle behavior
- sensors in a complete simulation
- mode testing
- mission flow
- repeatable debugging without hardware

## Practical conclusion

For "just get a feel for it on an RPi", the startup message is fine and expected.

The real question is not whether that line appears, but whether the process continues cleanly and whether the attached hardware matches what Rover expects.
