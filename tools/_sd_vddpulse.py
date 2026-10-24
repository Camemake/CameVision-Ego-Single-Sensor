#!/usr/bin/env python3
"""Drop microSD VDD on GPIO3_B4 (vcc3v3_sd), then re-identify."""
import mmap
import os
import struct
import time

GPIO3 = 0x21E00000
PIN = 12
# Rockchip GPIO v2
DR_L, DDR_L = 0x00, 0x08


def hiword(bit, val):
    return (1 << (bit + 16)) | ((val & 1) << bit)


def card():
    size = ""
    try:
        size = open("/sys/block/mmcblk1/size").read().strip()
    except OSError:
        pass
    typ = ocr = ""
    host = "/sys/class/mmc_host/mmc1"
    if os.path.isdir(host):
        for name in os.listdir(host):
            if name.startswith("mmc1:"):
                p = os.path.join(host, name)
                try:
                    typ = open(p + "/type").read().strip()
                    ocr = open(p + "/ocr").read().strip()
                except OSError:
                    pass
    return typ, ocr, size


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
    time.sleep(0.3)
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m = mmap.mmap(fd, 0x1000, offset=GPIO3)
    print("DR_L", hex(struct.unpack_from("<I", m, DR_L)[0]),
          "DDR_L", hex(struct.unpack_from("<I", m, DDR_L)[0]))
    # output + drive low (power off)
    struct.pack_into("<I", m, DDR_L, hiword(PIN, 1))
    struct.pack_into("<I", m, DR_L, hiword(PIN, 0))
    print("off DR_L", hex(struct.unpack_from("<I", m, DR_L)[0]))
    time.sleep(0.4)
    # drive high (power on)
    struct.pack_into("<I", m, DR_L, hiword(PIN, 1))
    print("on DR_L", hex(struct.unpack_from("<I", m, DR_L)[0]))
    time.sleep(0.05)
    m.close()
    os.close(fd)
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
    time.sleep(4)
    typ, ocr, size = card()
    print("AFTER type=%s ocr=%s size=%s" % (typ, ocr, size))
    os.system("dmesg | grep -E 'new SD|error -|mmcblk1' | tail -8")


if __name__ == "__main__":
    main()
