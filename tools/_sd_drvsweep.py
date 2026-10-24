#!/usr/bin/env python3
"""Restore CMD8 patches, then sweep TIMING_CON0 drive phase and re-identify."""
import mmap
import os
import struct
import time

PHYS = 0x40200000
OFF_BL = 0x5A7568
OFF_ARG = 0x5A879C
OFF_SKIP_DRV = 0x5B7358
OFF_DRVDEG = 0x5B7374
BL_ORIG = bytes.fromhex("24050094")
ORIG_ARG = bytes.fromhex("421580522100022a")
NOP = bytes.fromhex("1f2003d5")
B_HI_DRV = bytes.fromhex("68020054")


def map_off(fd, off, n=16):
    phys = PHYS + off
    page = phys & ~0xFFF
    rel = phys - page
    return mmap.mmap(fd, rel + n, offset=page), rel


def set_drive_insn(fd, degrees):
    m, rel = map_off(fd, OFF_DRVDEG, 12)
    m[rel : rel + 4] = struct.pack("<I", 0x52800000 | ((degrees & 0xFFFF) << 5) | 2)
    m[rel + 4 : rel + 8] = struct.pack("<I", 0x52800000 | ((degrees & 0xFFFF) << 5) | 1)
    m[rel + 8 : rel + 12] = NOP
    m.close()


def card():
    size = ""
    try:
        size = open("/sys/block/mmcblk1/size").read().strip()
    except OSError:
        pass
    typ = ocr = csd = ""
    host = "/sys/class/mmc_host/mmc1"
    if os.path.isdir(host):
        for name in os.listdir(host):
            if name.startswith("mmc1:"):
                p = os.path.join(host, name)
                def rd(fn):
                    try:
                        return open(os.path.join(p, fn)).read().strip()
                    except OSError:
                        return ""
                return rd("type"), rd("ocr"), rd("csd"), size
    return typ, ocr, csd, size


def main():
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m, rel = map_off(fd, OFF_BL)
    m[rel : rel + 4] = BL_ORIG
    print("bl restored", m[rel : rel + 4].hex())
    m.close()
    m, rel = map_off(fd, OFF_ARG, 8)
    m[rel : rel + 8] = ORIG_ARG
    print("arg restored")
    m.close()
    # do not skip drive-phase programming
    m, rel = map_off(fd, OFF_SKIP_DRV)
    print("drv skip", m[rel : rel + 4].hex())
    m[rel : rel + 4] = NOP
    m.close()

    os.system("umount /mnt/sdcard 2>/dev/null")
    for deg in (0, 45, 90, 135, 180, 225, 270, 315):
        set_drive_insn(fd, deg)
        os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
        time.sleep(0.4)
        os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
        time.sleep(2.0)
        typ, ocr, csd, size = card()
        print("DRV %d type=%s ocr=%s size=%s csd=%s" % (deg, typ, ocr, size, csd))
        if typ == "SDHC" or (size.isdigit() and int(size) > 20000000):
            print("SDHC_OK")
            break
    os.close(fd)
    os.system("dmesg | grep -E 'new SD|error -' | tail -12")


if __name__ == "__main__":
    main()
