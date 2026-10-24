#!/usr/bin/env python3
"""Slow SD 2.0 identify on sdmmc0 via /dev/mem. Unbinds 21d60000 only."""
import mmap
import os
import struct
import time

BASE = 0x21D60000
CTRL, PWREN, CLKDIV, CLKSRC, CLKENA = 0x00, 0x04, 0x08, 0x0C, 0x10
TMOUT, CTYPE, CMDARG, CMD = 0x14, 0x18, 0x28, 0x2C
RESP0, MINTSTS, RINTSTS, STATUS = 0x30, 0x40, 0x44, 0x48

CMD_START = 1 << 31
CMD_UPDATE_CLK = 1 << 21
CMD_SEND_INIT = 1 << 15
CMD_STOP = 1 << 14
CMD_PRV_DAT_WAIT = 1 << 13
CMD_RESP_CRC = 1 << 8
CMD_RESP_EXP = 1 << 6


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
    time.sleep(0.2)
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m = mmap.mmap(fd, 0x4000, offset=BASE)

    def rd(off):
        return struct.unpack_from("<I", m, off)[0]

    def wr(off, val):
        struct.pack_into("<I", m, off, val)

    def wait_cmd(ms=200):
        t0 = time.time()
        while time.time() - t0 < ms / 1000.0:
            if (rd(CMD) & CMD_START) == 0:
                return True
            time.sleep(0.001)
        return False

    def cmd(opcode, arg, flags, delay=0.02):
        wr(RINTSTS, 0xFFFFFFFF)
        wr(CMDARG, arg)
        wr(CMD, CMD_START | CMD_PRV_DAT_WAIT | flags | opcode)
        ok = wait_cmd()
        time.sleep(delay)
        st = rd(RINTSTS)
        resp = rd(RESP0)
        print("CMD%-2d arg=0x%08x rint=0x%08x resp=0x%08x %s" % (
            opcode, arg, st, resp, "ok" if ok else "BUSY"))
        return resp, st

    print("CTRL=0x%x STATUS=0x%x" % (rd(CTRL), rd(STATUS)))
    wr(TMOUT, 0xFFFFFFFF)
    wr(CTYPE, 0)
    cmd(0, 0, CMD_SEND_INIT, 0.05)
    r7 = None
    for i in range(12):
        resp, st = cmd(8, 0x1AA, CMD_RESP_EXP | CMD_RESP_CRC, 0.02)
        if (resp & 0xFF) == 0xAA and (st & 0xBF) == 0:
            r7 = resp
            print("CMD8 OK try", i)
            break
    ocr = 0
    for i in range(40):
        cmd(55, 0, CMD_RESP_EXP | CMD_RESP_CRC, 0.005)
        ocr, st = cmd(41, 0x40300000, CMD_RESP_EXP, 0.01)
        if ocr & 0x80000000:
            print("READY ocr=0x%08x CCS=%d" % (ocr, 1 if (ocr & 0x40000000) else 0))
            break
    m.close()
    os.close(fd)
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
    time.sleep(3)
    print("rebound")


if __name__ == "__main__":
    main()
