import os, termios, tty, struct, time, select

dev = "/dev/serial0"
fd = os.open(dev, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)

attrs = termios.tcgetattr(fd)
tty.setraw(fd)
attrs = termios.tcgetattr(fd)
attrs[4] = termios.B115200
attrs[5] = termios.B115200
termios.tcsetattr(fd, termios.TCSANOW, attrs)

buf = bytearray()
last_print = 0
latest = None

while True:
    r, _, _ = select.select([fd], [], [], 0.02)
    if r:
        try:
            buf.extend(os.read(fd, 512))
        except BlockingIOError:
            pass

    while len(buf) >= 32:
        if buf[0] != 0x20 or buf[1] != 0x40:
            buf.pop(0)
            continue

        frame = bytes(buf[:32])
        del buf[:32]

        checksum = 0xFFFF - sum(frame[:30])
        got = frame[30] | (frame[31] << 8)
        if checksum != got:
            continue

        latest = struct.unpack("<14H", frame[2:30])

    now = time.time()
    if latest and now - last_print >= 0.05:
        print(" ".join(f"CH{i+1}:{latest[i]:4d}" for i in range(8)), flush=True)
        last_print = now
