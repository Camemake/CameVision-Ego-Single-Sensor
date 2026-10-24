#!/usr/bin/env python3
"""Read sector 0 and 32 with raw CMD17 args (byte vs block)."""
import ctypes
import fcntl
import os

MMC_IOC_CMD = 0xC048B300
MMC_RSP_PRESENT = 1
MMC_RSP_CRC = 4
MMC_RSP_OPCODE = 16
MMC_CMD_ADTC = 1 << 5
MMC_RSP_R1 = MMC_RSP_PRESENT | MMC_RSP_CRC | MMC_RSP_OPCODE


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


def read17(fd, arg):
    buf = ctypes.create_string_buffer(512)
    c = Ioc()
    c.opcode = 17
    c.arg = arg
    c.flags = MMC_RSP_R1 | MMC_CMD_ADTC
    c.blksz = 512
    c.blocks = 1
    c.cmd_timeout_ms = 500
    c.data_ptr = ctypes.addressof(buf)
    try:
        fcntl.ioctl(fd, MMC_IOC_CMD, c)
        data = buf.raw
        print("ARG 0x%x resp=0x%x head=%s" % (arg, c.response[0], data[:16].hex()))
        return data
    except OSError as e:
        print("ARG 0x%x FAIL %s" % (arg, e))
        return None


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    fd = os.open("/dev/mmcblk1", os.O_RDWR)
    for arg in (0, 32, 129, 16384):
        read17(fd, arg)
    os.close(fd)


if __name__ == "__main__":
    main()
