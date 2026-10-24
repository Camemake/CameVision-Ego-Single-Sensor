#!/usr/bin/env python3
"""Sweep internal sample phase and re-identify. No CLKDIV patches."""
import mmap
import os
import struct
import time

PHYS = 0x40200000
OFF_SKIP = 0x5B7318
OFF_PHASE = 0x5B7330
B_HI = bytes.fromhex("c8010054")
NOP = bytes.fromhex("1f2003d5")
LDR_PHASE = bytes.fromhex("a11240b9")  # ldr w1, [x21, #0x10]


def map_off(fd, off, n=16):
    phys = PHYS + off
    page = phys & ~0xFFF
    rel = phys - page
    return mmap.mmap(fd, rel + n, offset=page), rel


def mov_w1(deg):
    return struct.pack("<I", 0x52800000 | ((deg & 0xFFFF) << 5) | 1)


def card():
    host = "/sys/class/mmc_host/mmc1"
    typ = ocr = csd = name = ""
    size = ""
    try:
        size = open("/sys/block/mmcblk1/size").read().strip()
    except OSError:
        pass
    if os.path.isdir(host):
        for name in os.listdir(host):
            p = os.path.join(host, name)
            if name.startswith("mmc1:") and os.path.isdir(p):
                def rd(fn):
                    try:
                        return open(os.path.join(p, fn)).read().strip()
                    except OSError:
                        return ""
                typ, ocr, csd, nm = rd("type"), rd("ocr"), rd("csd"), rd("name")
                return typ, ocr, csd, nm, size
    return typ, ocr, csd, name, size


def main():
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m, rel = map_off(fd, OFF_SKIP)
    print("skip", m[rel : rel + 4].hex())
    m[rel : rel + 4] = NOP
    m.close()
    os.system("umount /mnt/sdcard 2>/dev/null")
    for deg in (0, 45, 90, 135, 180, 225, 270, 315):
        m, rel = map_off(fd, OFF_PHASE)
        m[rel : rel + 4] = mov_w1(deg)
        print("phase insn", m[rel : rel + 4].hex(), "deg", deg)
        m.close()
        os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
        time.sleep(0.8)
        os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
        time.sleep(2.2)
        typ, ocr, csd, nm, size = card()
        print("DEG %d type=%s ocr=%s size=%s name=%s csd=%s" % (deg, typ, ocr, size, nm, csd))
        if typ == "SDHC" or (size.isdigit() and int(size) > 20000000):
            print("SDHC_OK")
            break
    os.close(fd)
    os.system("dmesg | grep 'new SD' | tail -8")


if __name__ == "__main__":
    main()
