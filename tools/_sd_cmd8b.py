#!/usr/bin/env python3
import ctypes
import fcntl
import os
import time

MMC_IOC_CMD = 0xC048B300
MMC_RSP_PRESENT = 1
MMC_RSP_CRC = 4
MMC_RSP_OPCODE = 16
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


def send(fd, opcode, arg, flags, acmd=0, sleep_ms=5, tmo=200):
    c = Ioc()
    c.opcode = opcode
    c.arg = arg
    c.flags = flags
    c.is_acmd = acmd
    c.cmd_timeout_ms = tmo
    c.postsleep_min_us = sleep_ms * 1000
    c.postsleep_max_us = sleep_ms * 1000 + 2000
    try:
        fcntl.ioctl(fd, MMC_IOC_CMD, c)
        print("CMD%s arg=0x%08x resp=0x%08x" % (opcode, arg, c.response[0]))
        return c.response[0]
    except OSError as e:
        print("CMD%s arg=0x%08x FAIL %s" % (opcode, arg, e))
        return None


def main():
    print("sizeof", ctypes.sizeof(Ioc))
    os.system("umount /mnt/sdcard 2>/dev/null")
    fd = os.open("/dev/mmcblk1", os.O_RDWR)
    send(fd, 0, 0, 0, sleep_ms=50)
    time.sleep(0.05)
    r7 = None
    for i in range(8):
        r = send(fd, 8, 0x1AA, MMC_RSP_R7 | MMC_CMD_BCR, sleep_ms=10)
        if r is not None and (r & 0xFF) == 0xAA:
            r7 = r
            print("CMD8 OK", i)
            break
    if r7 is None:
        print("CMD8 never 0xAA")
    for i in range(30):
        r = send(fd, 41, 0x40300000, MMC_RSP_R3 | MMC_CMD_BCR, acmd=1, sleep_ms=10)
        if r is None:
            break
        if r & 0x80000000:
            print("READY ocr=0x%08x CCS=%d" % (r, 1 if (r & 0x40000000) else 0))
            break
    os.close(fd)


if __name__ == "__main__":
    main()
