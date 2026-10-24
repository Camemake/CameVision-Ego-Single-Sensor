#!/usr/bin/env python3
"""CMD0+CMD8 on the live controller (stay bound so clocks stay on)."""
import ctypes
import fcntl
import mmap
import os
import struct
import time

SD = 0x21D60000
CMDARG, CMD, RESP0, RINTSTS = 0x28, 0x2C, 0x30, 0x44
CMD_START, CMD_WAIT, CMD_INIT = 1 << 31, 1 << 13, 1 << 15
CMD_CRC, CMD_RESP = 1 << 8, 1 << 6

MMC_IOC_CMD = 0xC048B300
MMC_RSP_R7 = 1 | 4 | 16
MMC_CMD_BCR = 3 << 5


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


def main():
    print("clk_rate", open("/sys/kernel/debug/clk/cclk_sdmmc0/clk_rate").read().strip())
    print("parent", open("/sys/kernel/debug/clk/cclk_sdmmc0/clk_parent").read().strip())
    for path in (
        "/sys/kernel/debug/mmc1/clock",
        "/sys/kernel/debug/mmc1/ios",
    ):
        try:
            print(path, open(path).read().strip()[:200])
        except OSError as e:
            print(path, e)
    try:
        open("/sys/kernel/debug/mmc1/clock", "w").write("400000\n")
        print("clock write ok", open("/sys/kernel/debug/mmc1/clock").read().strip())
    except OSError as e:
        print("clock write", e)

    os.system("umount /mnt/sdcard 2>/dev/null")
    fdmem = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    sd = mmap.mmap(fdmem, 0x4000, offset=SD)

    def rd(off):
        return struct.unpack_from("<I", sd, off)[0]

    def wr(off, val):
        struct.pack_into("<I", sd, off, val)

    print("USRID", hex(rd(0x68)), "STATUS", hex(rd(0x48)), "CTRL", hex(rd(0)),
          "CLKDIV", hex(rd(8)), "CON0", hex(rd(0x130)), "CON1", hex(rd(0x134)))

    def wait_cmd():
        t0 = time.time()
        while time.time() - t0 < 0.2:
            if (rd(CMD) & CMD_START) == 0:
                return True
            time.sleep(0.0005)
        return False

    def raw(op, arg, flags):
        wr(RINTSTS, 0xFFFFFFFF)
        wr(CMDARG, arg)
        wr(CMD, CMD_START | CMD_WAIT | flags | op)
        ok = wait_cmd()
        st, resp = rd(RINTSTS), rd(RESP0)
        print("RAW CMD%-2d arg=%08x rint=%08x resp=%08x %s" % (
            op, arg, st, resp, "ok" if ok else "BUSY"))
        return resp, st

    raw(0, 0, CMD_INIT)
    time.sleep(0.02)
    for i in range(5):
        raw(8, 0x1AA, CMD_RESP | CMD_CRC)
    sd.close()

    blk = os.open("/dev/mmcblk1", os.O_RDWR)
    c = Ioc()
    c.opcode = 0
    c.cmd_timeout_ms = 200
    c.postsleep_min_us = 20000
    c.postsleep_max_us = 25000
    try:
        fcntl.ioctl(blk, MMC_IOC_CMD, c)
        print("IOC CMD0 resp", hex(c.response[0]))
    except OSError as e:
        print("IOC CMD0", e)
    c = Ioc()
    c.opcode = 8
    c.arg = 0x1AA
    c.flags = MMC_RSP_R7 | MMC_CMD_BCR
    c.cmd_timeout_ms = 200
    try:
        fcntl.ioctl(blk, MMC_IOC_CMD, c)
        print("IOC CMD8 resp", hex(c.response[0]), hex(c.response[1]))
    except OSError as e:
        print("IOC CMD8", e)
    os.close(blk)
    os.close(fdmem)
    os.system("echo 1 > /sys/class/mmc_host/mmc1/force_rescan")
    time.sleep(3)
    os.system(
        "echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:b368/type 2>/dev/null); "
        "echo OCR=$(cat /sys/class/mmc_host/mmc1/mmc1:b368/ocr 2>/dev/null); "
        "echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)"
    )


if __name__ == "__main__":
    main()
