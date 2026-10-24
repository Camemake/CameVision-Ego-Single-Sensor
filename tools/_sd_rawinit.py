#!/usr/bin/env python3
"""Raw SD 2.0 identify on 21d60000 after unbind, with CRU clock forced on."""
import mmap
import os
import struct
import time

CRU = 0x20000000
CRU_GATE = 0x81C
GPIO3 = 0x21E00000
SD = 0x21D60000

CTRL, PWREN, CLKDIV, CLKENA = 0x00, 0x04, 0x08, 0x10
TMOUT, CTYPE, CMDARG, CMD = 0x14, 0x18, 0x28, 0x2C
RESP0, RINTSTS, STATUS = 0x30, 0x44, 0x48
USRID = 0x68
CON0, CON1 = 0x130, 0x134

CMD_START = 1 << 31
CMD_UPDATE = 1 << 21
CMD_INIT = 1 << 15
CMD_WAIT = 1 << 13
CMD_CRC = 1 << 8
CMD_RESP = 1 << 6


def hiword(bit, val):
    return (1 << (bit + 16)) | ((val & 1) << bit)


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
    time.sleep(0.3)

    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    cru = mmap.mmap(fd, 0x1000, offset=CRU)
    gpio = mmap.mmap(fd, 0x1000, offset=GPIO3)
    sd = mmap.mmap(fd, 0x4000, offset=SD)

    def crd(off):
        return struct.unpack_from("<I", cru, off)[0]

    def cwr(off, val):
        struct.pack_into("<I", cru, off, val)

    def rd(off):
        return struct.unpack_from("<I", sd, off)[0]

    def wr(off, val):
        struct.pack_into("<I", sd, off, val)

    # Pulse VDD GPIO3_B4
    struct.pack_into("<I", gpio, 0x08, hiword(12, 1))
    struct.pack_into("<I", gpio, 0x00, hiword(12, 0))
    time.sleep(0.3)
    struct.pack_into("<I", gpio, 0x00, hiword(12, 1))
    time.sleep(0.05)

    # Ungate cclk_sdmmc0 (bit 7 of CRU 0x81c). HIWORD_UPDATE.
    print("CRU81c before", hex(crd(CRU_GATE)))
    cwr(CRU_GATE, 0x00800000)
    print("CRU81c after", hex(crd(CRU_GATE)))

    print("USRID", hex(rd(USRID)), "STATUS", hex(rd(STATUS)), "CTRL", hex(rd(CTRL)))

    # Soft reset while clock is on
    wr(CTRL, 0x7)
    t0 = time.time()
    while time.time() - t0 < 0.2:
        if (rd(CTRL) & 0x7) == 0:
            break
        time.sleep(0.001)
    wr(CTRL, 0x30)
    wr(PWREN, 1)
    wr(TMOUT, 0xFFFFFFFF)
    wr(CTYPE, 0)
    wr(RINTSTS, 0xFFFFFFFF)
    print("CTRL after rst", hex(rd(CTRL)), "STATUS", hex(rd(STATUS)))

    def wait_cmd(ms=200):
        t0 = time.time()
        while time.time() - t0 < ms / 1000.0:
            if (rd(CMD) & CMD_START) == 0:
                return True
            time.sleep(0.0005)
        return False

    def update_clk():
        wr(CMD, CMD_START | CMD_UPDATE | CMD_WAIT)
        return wait_cmd(100)

    def set_div(div):
        wr(CLKENA, 0)
        update_clk()
        wr(CLKDIV, div)
        update_clk()
        wr(CLKENA, 0x00010001)
        update_clk()

    def set_phase(con, deg):
        n = (deg // 90) & 3
        rem = deg % 90
        delay = min(255, int(round(rem * (20000.0 / 90.0) / 60.0))) if rem else 0
        raw = n
        if delay:
            raw |= (1 << 10) | (delay << 2)
        raw <<= 1
        wr(con, (raw & 0xFFFF) | (0x0FFF << 16))

    def cmd(op, arg, flags, delay=0.01):
        wr(RINTSTS, 0xFFFFFFFF)
        wr(CMDARG, arg)
        wr(CMD, CMD_START | CMD_WAIT | flags | op)
        ok = wait_cmd()
        time.sleep(delay)
        st = rd(RINTSTS)
        resp = rd(RESP0)
        print("  CMD%-2d arg=%08x rint=%08x resp=%08x %s" % (
            op, arg, st, resp, "ok" if ok else "BUSY"))
        return resp, st, ok

    found = None
    for div in (0, 16, 31, 63):
        set_div(div)
        print("CLKDIV", div, "now", hex(rd(CLKDIV)), "CLKENA", hex(rd(CLKENA)))
        for ddeg in (90, 0, 180, 45, 135, 270):
            set_phase(CON0, ddeg)
            set_phase(CON1, 90)
            cmd(0, 0, CMD_INIT, 0.05)
            r7 = None
            for _ in range(6):
                resp, st, ok = cmd(8, 0x1AA, CMD_RESP | CMD_CRC, 0.01)
                if (resp & 0xFF) == 0xAA and (st & 0x1C2) == 0:
                    r7 = resp
                    break
            if r7 is None:
                continue
            print("CMD8 OK div", div, "drv", ddeg, "r7", hex(r7))
            ocr = 0
            for _ in range(40):
                cmd(55, 0, CMD_RESP | CMD_CRC, 0.002)
                ocr, st, ok = cmd(41, 0x40FF8000, CMD_RESP, 0.01)
                if ocr & 0x80000000:
                    break
            print("READY ocr=%08x CCS=%d" % (ocr, 1 if (ocr & 0x40000000) else 0))
            found = (div, ddeg, ocr)
            break
        if found:
            break

    print("RESULT", found)
    cru.close()
    gpio.close()
    sd.close()
    os.close(fd)
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
    time.sleep(3)
    os.system(
        "echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:b368/type 2>/dev/null); "
        "echo OCR=$(cat /sys/class/mmc_host/mmc1/mmc1:b368/ocr 2>/dev/null); "
        "echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)"
    )


if __name__ == "__main__":
    main()
