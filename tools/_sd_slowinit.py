#!/usr/bin/env python3
"""Identify this card at ~400 kHz with internal TIMING_CON phase sweep.

Do not unbind Wi-Fi. Only talk to 21d60000 / mmcblk1.
"""
import ctypes
import fcntl
import mmap
import os
import struct
import time

BASE = 0x21D60000
CTRL, CLKDIV, CLKENA = 0x00, 0x08, 0x10
CMDARG, CMD = 0x28, 0x2C
RINTSTS, STATUS = 0x44, 0x48
TIMING_CON1 = 0x134
CMD_START = 1 << 31
CMD_UPDATE_CLK = 1 << 21
CMD_PRV_DAT_WAIT = 1 << 13

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


def rd(m, off):
    return struct.unpack_from("<I", m, off)[0]


def wr(m, off, val):
    struct.pack_into("<I", m, off, val)


def wait_cmd(m, ms=100):
    t0 = time.time()
    while time.time() - t0 < ms / 1000.0:
        if (rd(m, CMD) & CMD_START) == 0:
            return True
        time.sleep(0.0005)
    return False


def update_clk(m):
    wr(m, CMD, CMD_START | CMD_UPDATE_CLK | CMD_PRV_DAT_WAIT)
    return wait_cmd(m)


def set_clkdiv(m, div):
    # disable clock, set divider, re-enable. Synopsys procedure.
    wr(m, CLKENA, 0)
    update_clk(m)
    wr(m, CLKDIV, div)
    update_clk(m)
    wr(m, CLKENA, 0x00010001)
    update_clk(m)


def set_phase(m, degrees):
    nineties = (degrees // 90) & 3
    remainder = degrees % 90
    delay_num = 0
    if remainder:
        # 12.5 MHz card clock: one 90deg ~= 20 ns; 60ps steps
        delay_num = min(255, int(round(remainder * (20000.0 / 90.0) / 60.0)))
    raw = nineties
    if delay_num:
        raw |= (1 << 10) | (delay_num << 2)
    raw <<= 1
    wr(m, TIMING_CON1, (raw & 0xFFFF) | (0x0FFF << 16))


def send(fd, opcode, arg, flags, acmd=0, sleep_ms=8):
    c = Ioc()
    c.opcode = opcode
    c.arg = arg
    c.flags = flags
    c.is_acmd = acmd
    c.cmd_timeout_ms = 250
    c.postsleep_min_us = sleep_ms * 1000
    c.postsleep_max_us = sleep_ms * 1000 + 2000
    try:
        fcntl.ioctl(fd, MMC_IOC_CMD, c)
        return c.response[0], None
    except OSError as e:
        return None, str(e)


def try_init(fd, m, label):
    send(fd, 0, 0, 0, sleep_ms=20)
    time.sleep(0.02)
    r7, e7 = send(fd, 8, 0x1AA, MMC_RSP_R7 | MMC_CMD_BCR)
    r3 = None
    e3 = None
    if r7 is not None and (r7 & 0xFF) == 0xAA:
        for _ in range(40):
            r3, e3 = send(fd, 41, 0x40FF8000, MMC_RSP_R3 | MMC_CMD_BCR, acmd=1)
            if r3 is None:
                break
            if r3 & 0x80000000:
                break
    print("%s CLKDIV=0x%x CON1=0x%x CMD8=%s %s ACMD41=%s %s" % (
        label, rd(m, CLKDIV), rd(m, TIMING_CON1),
        hex(r7) if r7 is not None else "FAIL", e7 or "",
        hex(r3) if r3 is not None else "FAIL", e3 or ""))
    if r3 is not None and (r3 & 0x80000000):
        print("READY ocr=0x%08x CCS=%d" % (r3, 1 if (r3 & 0x40000000) else 0))
        return True
    return r7 is not None and (r7 & 0xFF) == 0xAA


def main():
    print("clk_rate", open("/sys/kernel/debug/clk/cclk_sdmmc0/clk_rate").read().strip())
    try:
        open("/sys/kernel/debug/clk/cclk_sdmmc0/clk_rate", "w").write("800000")
        time.sleep(0.05)
        print("clk_rate after 800000", open("/sys/kernel/debug/clk/cclk_sdmmc0/clk_rate").read().strip())
    except OSError as e:
        print("clk_rate write", e)

    os.system("umount /mnt/sdcard 2>/dev/null")
    fdmem = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m = mmap.mmap(fdmem, 0x4000, offset=BASE)
    blk = os.open("/dev/mmcblk1", os.O_RDWR)
    print("CTRL=0x%x STATUS=0x%x CLKDIV=0x%x CLKENA=0x%x CON1=0x%x" % (
        rd(m, CTRL), rd(m, STATUS), rd(m, CLKDIV), rd(m, CLKENA), rd(m, TIMING_CON1)))

    ok = False
    for div in (16, 31, 63):
        set_clkdiv(m, div)
        time.sleep(0.01)
        print("set CLKDIV", div, "now", hex(rd(m, CLKDIV)), "CLKENA", hex(rd(m, CLKENA)))
        if try_init(blk, m, "div%d-ph90" % div):
            ok = True
            break
        for deg in (0, 45, 90, 135, 180, 225, 270, 315):
            set_phase(m, deg)
            if try_init(blk, m, "div%d-ph%d" % (div, deg)):
                ok = True
                break
        if ok:
            break

    set_clkdiv(m, 0)
    os.close(blk)
    m.close()
    os.close(fdmem)
    os.system("echo 1 > /sys/class/mmc_host/mmc1/force_rescan 2>/dev/null")
    time.sleep(2)
    os.system("cat /sys/class/mmc_host/mmc1/mmc1\\:0001/type; cat /sys/block/mmcblk1/size")
    print("DONE ok=%s" % ok)


if __name__ == "__main__":
    main()
