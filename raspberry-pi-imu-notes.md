# IMU for Raspberry Pi

## Recommendation

For most Raspberry Pi projects, use a `BNO085` or `BNO086` breakout board.

Why this is the best default choice:

- `9-DoF`: accelerometer, gyroscope, and magnetometer
- onboard sensor fusion, so orientation is easier to get working
- common breakout boards support `I2C`
- works well with Raspberry Pi `3.3V` logic

Good boards:

- Adafruit `BNO085 STEMMA QT`
- SparkFun `BNO086 Qwiic`

If you only need accel + gyro and want something simpler or cheaper:

- `ISM330DHCX`

Avoid using `MPU6050` unless you specifically need it. It is older and usually not the best choice for a new Raspberry Pi project.

## Raspberry Pi Wiring

Use `I2C`.

Raspberry Pi pins:

- `3.3V` power: physical pin `1`
- `GND`: physical pin `6`
- `SDA`: physical pin `3` / `GPIO2`
- `SCL`: physical pin `5` / `GPIO3`

Typical `BNO085/BNO086` to Raspberry Pi wiring:

| IMU Pin | Raspberry Pi Pin |
| --- | --- |
| `VIN` or `3V` | `3.3V` pin `1` |
| `GND` | `GND` pin `6` |
| `SDA` | `GPIO2 / SDA` pin `3` |
| `SCL` | `GPIO3 / SCL` pin `5` |

Notes:

- use `3.3V`, not `5V`, unless the board explicitly supports `5V` on `VIN`
- many boards already include pull-up resistors for `I2C`
- `STEMMA QT` and `Qwiic` boards are convenient because they are already wired for `I2C`

## Enable I2C on Raspberry Pi

Run:

```bash
sudo raspi-config
```

Then enable:

- `Interface Options`
- `I2C`

You can verify the IMU is visible with:

```bash
sudo apt-get install -y i2c-tools
i2cdetect -y 1
```

If the sensor is connected properly, you should see an address appear in the scan table.

## Python Example

Example using CircuitPython libraries on Raspberry Pi.

Install packages:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install adafruit-blinka adafruit-circuitpython-bno08x
```

Example script:

```python
import time
import board
from busio import I2C
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ACCELEROMETER
from adafruit_bno08x import BNO_REPORT_GYROSCOPE
from adafruit_bno08x import BNO_REPORT_MAGNETOMETER
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

i2c = I2C(board.SCL, board.SDA)
bno = BNO08X_I2C(i2c)

bno.enable_feature(BNO_REPORT_ACCELEROMETER)
bno.enable_feature(BNO_REPORT_GYROSCOPE)
bno.enable_feature(BNO_REPORT_MAGNETOMETER)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

while True:
    ax, ay, az = bno.acceleration
    gx, gy, gz = bno.gyro
    mx, my, mz = bno.magnetic
    qi, qj, qk, qr = bno.quaternion

    print(f"accel: {ax:.2f}, {ay:.2f}, {az:.2f} m/s^2")
    print(f"gyro:  {gx:.3f}, {gy:.3f}, {gz:.3f} rad/s")
    print(f"mag:   {mx:.2f}, {my:.2f}, {mz:.2f} uT")
    print(f"quat:  {qi:.4f}, {qj:.4f}, {qk:.4f}, {qr:.4f}")
    print()

    time.sleep(0.5)
```

## Practical Pick

Choose `BNO085/BNO086` if you want:

- stable orientation
- robotics or rover heading
- less time spent implementing your own fusion stack

Choose `ISM330DHCX` if you want:

- basic motion sensing only
- no magnetometer
- lower cost and simpler data handling

## References

- Raspberry Pi I2C docs: <https://www.raspberrypi.com/documentation/hardware/raspberrypi/i2c/README.md>
- Adafruit BNO085: <https://www.adafruit.com/product/4754>
- SparkFun BNO086 Qwiic: <https://www.sparkfun.com/sparkfun-vr-imu-breakout-bno086-qwiic.html>
- Adafruit ISM330DHCX: <https://www.adafruit.com/product/4502>
