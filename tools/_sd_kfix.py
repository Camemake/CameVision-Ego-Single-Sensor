#!/usr/bin/env python3
"""Live-patch sdmmc0 identify clock + internal sample phase.

Do not touch Wi-Fi (mmc2) or eMMC. Phys = 0x40200000 + Image offset.
"""
import mmap
import os
import struct
import time

PHYS_BASE = 0x40200000
PAGE = 0x1000

# file offset == VA & 0x00FFFFFF for this Image
OFF_DIV0 = 0x5B39BC          # mov w20,#0  when bus_hz==clock
OFF_PHASE_SKIP = 0x5B7318    # b.hi skip sample phase if ciu-sample missing
OFF_HCS = 0x5A756C           # cbnz after CMD8 (already nop in FIT)

MOV_W20_0 = bytes.fromhex("14008052")   # mov w20, #0
MOV_W20_16 = bytes.fromhex("14028052")  # mov w20, #16
NOP = bytes.fromhex("1f2003d5")


def map_at(fd, off, size=0x1000):
    page = off & ~(PAGE - 1)
    rel = off - page
    m = mmap.mmap(fd, rel + size, offset=page)
    return m, rel


def main():
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m, rel = map_at(fd, PHYS_BASE + OFF_DIV0)
    cur = m[rel : rel + 4]
    print("div0", cur.hex(), "expect", MOV_W20_0.hex())
    if cur not in (MOV_W20_0, MOV_W20_16):
        raise SystemExit("unexpected div0 insn")
    m[rel : rel + 4] = MOV_W20_16
    print("div0 ->", m[rel : rel + 4].hex())
    m.close()

    m, rel = map_at(fd, PHYS_BASE + OFF_PHASE_SKIP)
    cur = m[rel : rel + 4]
    print("phase_skip", cur.hex())
    m[rel : rel + 4] = NOP
    print("phase_skip -> nop", m[rel : rel + 4].hex())
    m.close()

    m, rel = map_at(fd, PHYS_BASE + OFF_HCS)
    print("hcs", m[rel : rel + 4].hex())
    m.close()
    os.close(fd)

    os.system("umount /mnt/sdcard 2>/dev/null")
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
    time.sleep(1)
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
    time.sleep(4)
    print("=== dmesg ===")
    os.system("dmesg | grep -E 'mmc1|21d60000' | tail -20")
    print("=== card ===")
    os.system(
        "cat /sys/class/mmc_host/mmc1/mmc1:0001/type; "
        "cat /sys/class/mmc_host/mmc1/mmc1:0001/name; "
        "cat /sys/class/mmc_host/mmc1/mmc1:0001/ocr; "
        "cat /sys/class/mmc_host/mmc1/mmc1:0001/csd; "
        "cat /sys/block/mmcblk1/size"
    )


if __name__ == "__main__":
    main()
