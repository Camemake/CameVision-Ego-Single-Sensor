#!/usr/bin/env python3
"""Clamp sdmmc0 bus_hz so identify CLKDIV is ~400 kHz, then rebind mmc1 only."""
import mmap
import os
import struct
import time

PHYS = 0x40200000
PAGE = 0x1000
OFF_LSR = 0x5B72F8
OFF_CAVE = 0x5B73EC
OFF_DIV0 = 0x5B39BC
B_TO_CAVE = struct.pack("<I", 0x1400003D)  # b 0x5B73EC from 0x5B72F8
LSR = bytes.fromhex("00fc41d3")
MOV_W20_0 = bytes.fromhex("14008052")
MOV_W20_16 = bytes.fromhex("14028052")

# lsr #1; if (bus_hz < 1e6) bus_hz = 12500000; b back to ldr
CAVE = [
    0xD341FC00,  # lsr x0, x0, #1
    0x52884801,  # mov w1, #0x4240
    0x72A001E1,  # movk w1, #0xf, lsl #16     ; 1000000
    0x6B01001F,  # cmp w0, w1
    0x54000062,  # b.hs +3
    0x52978400,  # mov w0, #0xbc20
    0x72A017C0,  # movk w0, #0xbe, lsl #16    ; 12500000
    0x17FFFFBD,  # b 0x5B72FC
]


def map_abs(fd, phys, size):
    page = phys & ~(PAGE - 1)
    rel = phys - page
    return mmap.mmap(fd, rel + size, offset=page), rel


def main():
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m, rel = map_abs(fd, PHYS + OFF_DIV0, 8)
    print("div0", m[rel : rel + 4].hex())
    if m[rel : rel + 4] == MOV_W20_16:
        m[rel : rel + 4] = MOV_W20_0
        print("div0 restored")
    m.close()

    m, rel = map_abs(fd, PHYS + OFF_LSR, 8)
    print("lsr", m[rel : rel + 4].hex())
    m[rel : rel + 4] = B_TO_CAVE
    print("lsr -> b cave")
    m.close()

    blob = b"".join(struct.pack("<I", w) for w in CAVE)
    m, rel = map_abs(fd, PHYS + OFF_CAVE, 64)
    m[rel : rel + len(blob)] = blob
    print("cave", m[rel : rel + len(blob)].hex())
    m.close()

    mm, _ = map_abs(fd, 0x21D60000, 0x80)
    ctrl = struct.unpack_from("<I", mm, 0)[0]
    print("CTRL", hex(ctrl))
    struct.pack_into("<I", mm, 0, 0x7)
    time.sleep(0.02)
    struct.pack_into("<I", mm, 0, 0x30)
    print("CTRL now", hex(struct.unpack_from("<I", mm, 0)[0]))
    mm.close()
    os.close(fd)

    os.system("umount /mnt/sdcard 2>/dev/null")
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
    time.sleep(1)
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
    time.sleep(6)
    os.system("dmesg | grep -E 'mmc1|21d60000' | tail -20")
    os.system(
        "echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/type 2>/dev/null); "
        "echo OCR=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/ocr 2>/dev/null); "
        "echo CSD=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/csd 2>/dev/null); "
        "echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)"
    )


if __name__ == "__main__":
    main()
