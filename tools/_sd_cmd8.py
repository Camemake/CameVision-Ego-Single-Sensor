#!/usr/bin/env python3
"""Send CMD8 + ACMD41(HCS) to the inserted card. Allowed board only."""
import ctypes
import fcntl
import os
import sys

MMC_BLOCK_MAJOR = 179
MMC_IOC_CMD = 0xC048B300  # _IOWR(179, 0, 72-byte mmc_ioc_cmd) aarch64

MMC_RSP_PRESENT = 1 << 0
MMC_RSP_CRC = 1 << 2
MMC_RSP_OPCODE = 1 << 4
MMC_RSP_136 = 1 << 1
MMC_CMD_AC = 0 << 5
MMC_CMD_BCR = 3 << 5
MMC_RSP_R1 = MMC_RSP_PRESENT | MMC_RSP_CRC | MMC_RSP_OPCODE
MMC_RSP_R3 = MMC_RSP_PRESENT
MMC_RSP_R7 = MMC_RSP_PRESENT | MMC_RSP_CRC | MMC_RSP_OPCODE


class Ioc(ctypes.Structure):
    _fields_ = [
        ("write_flag", ctypes.c_int),
        ("is_acmd", ctypes.c_int),
        ("opcode", ctypes.c_uint),
        ("arg", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("postsleep_min_us", ctypes.c_uint),
        ("postsleep_max_us", ctypes.c_uint),
        ("data_timeout_ns", ctypes.c_uint),
        ("cmd_timeout_ms", ctypes.c_uint),
        ("pad", ctypes.c_uint),
        ("response", ctypes.c_uint * 4),
        ("blksz", ctypes.c_uint),
        ("blocks", ctypes.c_uint),
        ("data_ptr", ctypes.c_uint64),
    ]


def send(fd, opcode, arg, flags, acmd=0, sleep_ms=0):
    c = Ioc()
    c.opcode = opcode
    c.arg = arg
    c.flags = flags
    c.is_acmd = acmd
    if sleep_ms:
        c.postsleep_min_us = sleep_ms * 1000
        c.postsleep_max_us = sleep_ms * 1000 + 1000
    try:
        fcntl.ioctl(fd, MMC_IOC_CMD, c)
        print("CMD%s arg=0x%08x resp=0x%08x 0x%08x 0x%08x 0x%08x" % (
            opcode, arg, c.response[0], c.response[1], c.response[2], c.response[3]))
        return c.response[0]
    except OSError as e:
        print("CMD%s arg=0x%08x FAIL %s" % (opcode, arg, e))
        return None


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    fd = os.open("/dev/mmcblk1", os.O_RDWR)
    print("open mmcblk1")
    send(fd, 0, 0, 0, sleep_ms=10)
    r7 = send(fd, 8, 0x1AA, MMC_RSP_R7 | MMC_CMD_BCR)
    ocr = 0x40300000
    for i in range(20):
        r3 = send(fd, 41, ocr, MMC_RSP_R3 | MMC_CMD_BCR, acmd=1, sleep_ms=10)
        if r3 is None:
            break
        if r3 & 0x80000000:
            print("READY ocr=0x%08x CCS=%d" % (r3, 1 if (r3 & 0x40000000) else 0))
            break
    os.close(fd)
    os.system("echo 1 > /sys/class/mmc_host/mmc1/force_rescan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
