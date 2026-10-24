#!/usr/bin/env python3
"""PIO-read 512B at block args 0, 32, 129 after a working CMD8 init."""
import mmap
import os
import struct
import time

SD = 0x21D60000
CTRL, CLKDIV, CLKENA = 0x00, 0x08, 0x10
TMOUT, CTYPE, BLKSIZ, BYTCNT = 0x14, 0x18, 0x1C, 0x20
CMDARG, CMD, RESP0, RINTSTS = 0x28, 0x2C, 0x30, 0x44
STATUS, FIFOTH, DATA = 0x48, 0x4C, 0x200
CMD_START, CMD_WAIT, CMD_INIT = 1 << 31, 1 << 13, 1 << 15
CMD_CRC, CMD_RESP, CMD_DATA = 1 << 8, 1 << 6, 1 << 9


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    open("/sys/kernel/debug/mmc1/clock", "w").write("400000\n")
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    sd = mmap.mmap(fd, 0x4000, offset=SD)

    def rd(o):
        return struct.unpack_from("<I", sd, o)[0]

    def wr(o, v):
        struct.pack_into("<I", sd, o, v)

    def wait():
        t0 = time.time()
        while time.time() - t0 < 0.3:
            if (rd(CMD) & CMD_START) == 0:
                return True
            time.sleep(0.0003)
        return False

    def cmd(op, arg, flags, delay=0.006):
        wr(RINTSTS, 0xFFFFFFFF)
        wr(CMDARG, arg)
        wr(CMD, CMD_START | CMD_WAIT | flags | op)
        ok = wait()
        time.sleep(delay)
        print("CMD%-2d arg=%08x rint=%08x resp=%08x" % (op, arg, rd(RINTSTS), rd(RESP0)))
        return rd(RESP0)

    # disable IDMAC, use PIO
    wr(0x8C, 0)  # BMOD
    wr(CTRL, rd(CTRL) | 0x2)  # fifo reset
    time.sleep(0.002)
    wr(CTRL, (rd(CTRL) & ~0x20) | 0x10)  # no DMA, use FIFO

    cmd(0, 0, CMD_INIT, 0.03)
    for _ in range(4):
        if (cmd(8, 0x1AA, CMD_RESP | CMD_CRC) & 0xFF) == 0xAA:
            print("CMD8_OK")
            break
    for _ in range(40):
        cmd(55, 0, CMD_RESP | CMD_CRC, 0.003)
        ocr = cmd(41, 0x40FF8000, CMD_RESP, 0.008)
        if ocr & 0x80000000:
            print("CCS", 1 if (ocr & 0x40000000) else 0)
            break
    cmd(2, 0, CMD_RESP | (1 << 7))
    rca = cmd(3, 0, CMD_RESP | CMD_CRC) & 0xFFFF0000
    cmd(7, rca, CMD_RESP | CMD_CRC)
    cmd(16, 512, CMD_RESP | CMD_CRC)
    wr(BLKSIZ, 512)
    wr(BYTCNT, 512)

    def pio_read(arg):
        wr(RINTSTS, 0xFFFFFFFF)
        wr(BLKSIZ, 512)
        wr(BYTCNT, 512)
        wr(CMDARG, arg)
        wr(CMD, CMD_START | CMD_WAIT | CMD_RESP | CMD_CRC | CMD_DATA | 17)
        wait()
        buf = bytearray()
        t0 = time.time()
        while len(buf) < 512 and time.time() - t0 < 0.4:
            st = rd(STATUS)
            # bit 2 = fifo empty?
            if (st & 0x4) == 0:
                buf += struct.pack("<I", rd(DATA))
            else:
                time.sleep(0.0002)
        print("READ arg=%d rint=%08x n=%d head=%s" % (
            arg, rd(RINTSTS), len(buf), bytes(buf[:16]).hex() if buf else ""))
        if len(buf) >= 512:
            print("  tail", bytes(buf[510:512]).hex(), "55aa" if buf[510:512] == b"\x55\xaa" else "")
        return bytes(buf)

    for a in (0, 32, 129, 16384):
        pio_read(a)
    sd.close()
    os.close(fd)
    os.system("echo 1 > /sys/class/mmc_host/mmc1/force_rescan")
    time.sleep(3)
    os.system("sh /userdata/camevision-sd.sh; echo SIZE=$(cat /sys/block/mmcblk1/size)")


if __name__ == "__main__":
    main()
