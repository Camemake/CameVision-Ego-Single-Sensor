#!/usr/bin/env python3
"""Dump sdmmc0 timing regs, then sweep TIMING_CON1 and try CMD8.

Keeps the dwmmc driver bound so clocks stay on. Allowed board only.
"""
import ctypes
import fcntl
import mmap
import os
import struct
import time

BASE = 0x21D60000
EMMC = 0x21470000
CTRL, PWREN, CLKDIV, CLKSRC, CLKENA = 0x00, 0x04, 0x08, 0x0C, 0x10
TMOUT, CTYPE, CMDARG, CMD = 0x14, 0x18, 0x28, 0x2C
RESP0, RINTSTS, STATUS = 0x30, 0x44, 0x48
USRID, VERID = 0x68, 0x6C
UHS_REG, RST_N = 0x74, 0x78
CLKSEL = 0x102C
TIMING_CON0, TIMING_CON1, MISC_CON = 0x130, 0x134, 0x138
HIWORD_UPDATE_MASK = 0xFFFF0000

MMC_IOC_CMD = 0xC048B300
MMC_RSP_PRESENT = 1
MMC_RSP_CRC = 4
MMC_RSP_OPCODE = 16
MMC_CMD_BCR = 3 << 5
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


def dump(m, name):
    offs = [
        CTRL, PWREN, CLKDIV, CLKSRC, CLKENA, TMOUT, CTYPE, 0x24, CMDARG, CMD,
        RESP0, RINTSTS, STATUS, USRID, VERID, UHS_REG, RST_N,
        TIMING_CON0, TIMING_CON1, MISC_CON, CLKSEL, 0x108, 0x110,
    ]
    print("=== %s ===" % name)
    for off in offs:
        print("  %04x = 0x%08x" % (off, struct.unpack_from("<I", m, off)[0]))


def hiword_update(val, mask, shift):
    return ((val & mask) << shift) | (mask << (shift + 16))


def set_internal_phase(m, degrees):
    # Rockchip TIMING_CON1: bits[2:1]=degree/90, bit10=delay_sel, bits[9:2]=delaynum
    deg = (degrees // 90) & 3
    # HIWORD_UPDATE style used by vendor: write mask in upper 16
    raw = hiword_update(deg, 0x3, 1)
    struct.pack_into("<I", m, TIMING_CON1, raw)


def send(fd, opcode, arg, flags, acmd=0, sleep_ms=8):
    c = Ioc()
    c.opcode = opcode
    c.arg = arg
    c.flags = flags
    c.is_acmd = acmd
    c.cmd_timeout_ms = 200
    c.postsleep_min_us = sleep_ms * 1000
    c.postsleep_max_us = sleep_ms * 1000 + 2000
    try:
        fcntl.ioctl(fd, MMC_IOC_CMD, c)
        return c.response[0], None
    except OSError as e:
        return None, str(e)


def main():
    fdmem = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    sd = mmap.mmap(fdmem, 0x4000, offset=BASE)
    em = mmap.mmap(fdmem, 0x4000, offset=EMMC)
    dump(sd, "sdmmc0")
    dump(em, "emmc")

    os.system("umount /mnt/sdcard 2>/dev/null")
    blk = os.open("/dev/mmcblk1", os.O_RDWR)
    print("=== phase sweep CMD0/CMD8/ACMD41 ===")
    found = None
    for deg in (0, 90, 180, 270):
        set_internal_phase(sd, deg)
        time.sleep(0.01)
        t1 = struct.unpack_from("<I", sd, TIMING_CON1)[0]
        send(blk, 0, 0, 0, sleep_ms=20)
        time.sleep(0.02)
        r7, e7 = send(blk, 8, 0x1AA, MMC_RSP_R7 | MMC_CMD_BCR)
        r3, e3 = send(blk, 41, 0x40300000, MMC_RSP_R3 | MMC_CMD_BCR, acmd=1)
        print("deg=%d CON1=0x%08x CMD8=%s %s ACMD41=%s %s" % (
            deg, t1, hex(r7) if r7 is not None else "FAIL", e7 or "",
            hex(r3) if r3 is not None else "FAIL", e3 or ""))
        if r7 is not None and (r7 & 0xFF) == 0xAA:
            found = deg
            if r3 is not None and (r3 & 0x80000000):
                print("READY deg=%d ocr=0x%08x CCS=%d" % (
                    deg, r3, 1 if (r3 & 0x40000000) else 0))
                break
    os.close(blk)
    if found is None:
        print("NO_CMD8")
    else:
        print("CMD8_OK deg", found)
    sd.close()
    em.close()
    os.close(fdmem)


if __name__ == "__main__":
    main()
