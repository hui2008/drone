import spidev
import time
import math

# MPU-6500 registers
WHO_AM_I      = 0x75
PWR_MGMT_1    = 0x6B
CONFIG        = 0x1A
GYRO_CONFIG   = 0x1B
ACCEL_CONFIG  = 0x1C
ACCEL_XOUT_H  = 0x3B

# SPI setup: bus 0, CE0 = /dev/spidev0.0
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1_000_000
spi.mode = 0b00

def read_reg(reg):
    # SPI read: bit 7 = 1
    return spi.xfer2([reg | 0x80, 0x00])[1]

def write_reg(reg, value):
    # SPI write: bit 7 = 0
    spi.xfer2([reg & 0x7F, value & 0xFF])

def read_bytes(reg, length):
    # First byte is command, following bytes are returned data
    data = spi.xfer2([reg | 0x80] + [0x00] * length)
    return data[1:]

def to_int16(high, low):
    value = (high << 8) | low
    if value & 0x8000:
        value -= 65536
    return value

def init_mpu6500():
    who = read_reg(WHO_AM_I)
    print(f"WHO_AM_I = 0x{who:02X}")

    if who != 0x70:
        print("Warning: expected 0x70 for MPU-6500")

    # Wake up device
    write_reg(PWR_MGMT_1, 0x00)
    time.sleep(0.1)

    # Basic digital low pass filter config
    write_reg(CONFIG, 0x03)

    # Gyro full-scale: ±250 deg/s
    # GYRO_CONFIG bits [4:3] = 00
    write_reg(GYRO_CONFIG, 0x00)

    # Accel full-scale: ±2g
    # ACCEL_CONFIG bits [4:3] = 00
    write_reg(ACCEL_CONFIG, 0x00)

    time.sleep(0.1)

def read_sensor():
    # Read 14 bytes:
    # accel x/y/z, temp, gyro x/y/z
    data = read_bytes(ACCEL_XOUT_H, 14)

    ax_raw = to_int16(data[0], data[1])
    ay_raw = to_int16(data[2], data[3])
    az_raw = to_int16(data[4], data[5])

    temp_raw = to_int16(data[6], data[7])

    gx_raw = to_int16(data[8], data[9])
    gy_raw = to_int16(data[10], data[11])
    gz_raw = to_int16(data[12], data[13])

    # Because we configured:
    # accel ±2g: 16384 LSB/g
    # gyro ±250 deg/s: 131 LSB/(deg/s)
    ax_g = ax_raw / 16384.0
    ay_g = ay_raw / 16384.0
    az_g = az_raw / 16384.0

    gx_dps = gx_raw / 131.0
    gy_dps = gy_raw / 131.0
    gz_dps = gz_raw / 131.0

    # MPU temperature formula, approximate
    temp_c = (temp_raw / 333.87) + 21.0

    return ax_g, ay_g, az_g, gx_dps, gy_dps, gz_dps, temp_c

try:
    init_mpu6500()

    while True:
        ax, ay, az, gx, gy, gz, temp = read_sensor()

        print(
            f"ACCEL g: X={ax:+.3f} Y={ay:+.3f} Z={az:+.3f} | "
            f"GYRO dps: X={gx:+.2f} Y={gy:+.2f} Z={gz:+.2f} | "
            f"TEMP={temp:.1f}C"
        )

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nStopped")

finally:
    spi.close()