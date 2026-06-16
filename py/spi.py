import spidev
import time

WHO_AM_I = 0x75

spi = spidev.SpiDev()
spi.open(0, 0)          # bus 0, CE0
spi.max_speed_hz = 1000000
spi.mode = 0b00

def read_reg(reg):
    # For MPU SPI read, set bit 7 = 1
    resp = spi.xfer2([reg | 0x80, 0x00])
    return resp[1]

time.sleep(0.1)

who = read_reg(WHO_AM_I)
print(f"WHO_AM_I = 0x{who:02X}")

if who == 0x70:
    print("Likely MPU-6500")
elif who == 0x71:
    print("Likely MPU-9250")
elif who == 0x73:
    print("Likely MPU-9255")
else:
    print("Unknown or wiring/SPI issue")

spi.close()
