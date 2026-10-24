#!/usr/bin/env python3
"""Diff CRU regs while sdmmc0 is bound vs unbound so we can keep clocks on."""
import mmap
import os
import struct
import time

CRU = 0x20000000
# RV1126B CRU is large; clock mux/div/gate for SDMMC is usually in the
# first 0x800 plus GATE_CON around 0x800-0xA00. Dump 0x1000.
SIZE = 0x1000


def snap(m):
    return [struct.unpack_from("<I", m, i)[0] for i in range(0, SIZE, 4)]


def main():
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m = mmap.mmap(fd, SIZE, offset=CRU)
    a = snap(m)
    os.system("umount /mnt/sdcard 2>/dev/null")
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
    time.sleep(0.5)
    b = snap(m)
    print("=== CRU diffs after unbind ===")
    n = 0
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print("%04x %08x -> %08x" % (i * 4, x, y))
            n += 1
    print("ndiff", n)
    # restore clocks to bound values, then we can bitbang later
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
    time.sleep(3)
    m.close()
    os.close(fd)
    os.system(
        "echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null); "
        "echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:b368/type 2>/dev/null)"
    )


if __name__ == "__main__":
    main()
