# Raspberry Pi Zero 2 W PREEMPT_RT Kernel

This note describes how to use Raspberry Pi OS Lite with a PREEMPT_RT Linux
kernel on a Raspberry Pi Zero 2 W, including a container-based cross-compile
workflow.

PREEMPT_RT is the modern real-time Linux kernel configuration. It is different
from the old RTLinux project. Raspberry Pi OS Lite does not provide a simple
`raspi-config` switch for this; the usual approach is to build and boot a
kernel with `CONFIG_PREEMPT_RT=y`.

## Choose 32-bit or 64-bit

On the Pi, check the running architecture:

```sh
uname -m
uname -r
```

For a Pi Zero 2 W:

- 32-bit Raspberry Pi OS Lite normally uses `kernel7.img`, `ARCH=arm`, and
  `bcm2709_defconfig`.
- 64-bit Raspberry Pi OS Lite normally uses `kernel8.img`, `ARCH=arm64`, and
  `bcm2711_defconfig`.

For most Pi Zero 2 W deployments, 32-bit Raspberry Pi OS Lite is a good default
because it is lighter on memory.

## Build in a container

Run the container from the directory where you want the kernel source and build
outputs to live:

```sh
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  debian:bookworm
```

Inside the container, install the common build dependencies:

```sh
apt update
apt install -y git bc bison flex libssl-dev make libncurses5-dev
```

Install the cross compiler for the target OS.

For 32-bit Raspberry Pi OS Lite:

```sh
apt install -y crossbuild-essential-armhf
```

For 64-bit Raspberry Pi OS Lite:

```sh
apt install -y crossbuild-essential-arm64
```

## Get the Raspberry Pi kernel source

Inside the container:

```sh
git clone --depth=1 https://github.com/raspberrypi/linux.git
cd linux
```

If the target Pi must stay close to its currently installed Raspberry Pi OS
kernel, use a Raspberry Pi kernel branch or tag that matches `uname -r` on the
Pi as closely as possible.

## Configure 32-bit Pi Zero 2 W

Use this section for 32-bit Raspberry Pi OS Lite.

```sh
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
export KERNEL=kernel7

make bcm2709_defconfig
make menuconfig
```

In `menuconfig`, enable:

```text
General setup
  Preemption Model
    Fully Preemptible Kernel (Real-Time)
```

Optionally set a local version so the booted kernel is easy to identify:

```text
General setup
  Local version - append to kernel release
    -rt
```

Save the configuration, then build:

```sh
make -j$(nproc) zImage modules dtbs
```

Install modules into a staging directory:

```sh
mkdir -p /work/pi-kernel-out
make INSTALL_MOD_PATH=/work/pi-kernel-out modules_install
```

The kernel image is:

```text
arch/arm/boot/zImage
```

The device trees and overlays are under:

```text
arch/arm/boot/dts/
```

## Configure 64-bit Pi Zero 2 W

Use this section for 64-bit Raspberry Pi OS Lite.

```sh
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-
export KERNEL=kernel8

make bcm2711_defconfig
make menuconfig
```

In `menuconfig`, enable:

```text
General setup
  Preemption Model
    Fully Preemptible Kernel (Real-Time)
```

Optionally set:

```text
General setup
  Local version - append to kernel release
    -rt
```

Save the configuration, then build:

```sh
make -j$(nproc) Image modules dtbs
```

Install modules into a staging directory:

```sh
mkdir -p /work/pi-kernel-out
make INSTALL_MOD_PATH=/work/pi-kernel-out modules_install
```

The kernel image is:

```text
arch/arm64/boot/Image
```

The device trees and overlays are under:

```text
arch/arm64/boot/dts/
```

## If PREEMPT_RT is not available

If `Fully Preemptible Kernel (Real-Time)` is not shown in `menuconfig`, the
selected Raspberry Pi kernel tree does not include the needed RT support. In
that case, apply the matching PREEMPT_RT patch from:

```text
https://cdn.kernel.org/pub/linux/kernel/projects/rt/
```

The RT patch version must closely match the Linux kernel version being built.
Do not mix arbitrary patch and kernel versions.

## Copy the kernel to the Pi

Examples below assume the Pi is reachable as `raspberrypi.local`.

For 32-bit:

```sh
scp arch/arm/boot/zImage pi@raspberrypi.local:/home/pi/kernel7-rt.img
scp -r /work/pi-kernel-out/lib/modules pi@raspberrypi.local:/home/pi/modules
```

For 64-bit:

```sh
scp arch/arm64/boot/Image pi@raspberrypi.local:/home/pi/kernel8-rt.img
scp -r /work/pi-kernel-out/lib/modules pi@raspberrypi.local:/home/pi/modules
```

Device tree files and overlays may also need to be copied if they differ from
the installed Raspberry Pi OS version. Keep a backup of the existing boot files
before replacing them.

## Install on the Pi

On the Pi, back up the existing kernel and install the new one.

For 32-bit:

```sh
sudo cp /boot/firmware/kernel7.img /boot/firmware/kernel7-backup.img
sudo cp ~/kernel7-rt.img /boot/firmware/kernel7-rt.img
sudo cp -r ~/modules/* /lib/modules/
```

For 64-bit:

```sh
sudo cp /boot/firmware/kernel8.img /boot/firmware/kernel8-backup.img
sudo cp ~/kernel8-rt.img /boot/firmware/kernel8-rt.img
sudo cp -r ~/modules/* /lib/modules/
```

Edit the boot config:

```sh
sudo nano /boot/firmware/config.txt
```

For 32-bit, add:

```ini
kernel=kernel7-rt.img
```

For 64-bit, add:

```ini
kernel=kernel8-rt.img
```

Reboot:

```sh
sudo reboot
```

## Verify PREEMPT_RT

After reboot:

```sh
uname -a
zcat /proc/config.gz | grep PREEMPT_RT
```

Expected:

```text
CONFIG_PREEMPT_RT=y
```

Optional latency test:

```sh
sudo apt update
sudo apt install rt-tests
sudo cyclictest -p 80 -t1 -n -i 1000 -l 10000
```

## Recovery

If the Pi does not boot with the RT kernel, mount the boot partition on another
machine and remove or comment the custom `kernel=...` line in
`/boot/firmware/config.txt`. The Pi will fall back to the default Raspberry Pi
OS kernel image.

