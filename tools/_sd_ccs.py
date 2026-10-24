#!/usr/bin/env python3
"""Hold 400 kHz, CMD0, retry CMD8, ACMD41(HCS). Print CCS."""
import mmap
import os
import struct
import time

SD = 0x21D60000
CMDARG, CMD, RESP0, RINTSTS = 0x28, 0x2C, 0x30, 0x44
CMD_START, CMD_WAIT, CMD_INIT = 1 << 31, 1 << 13, 1 << 15
CMD_CRC, CMD_RESP = 1 << 8, 1 << 6


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    open("/sys/kernel/debug/mmc1/clock", "w").write("400000\n")
    print("clock", open("/sys/kernel/debug/mmc1/clock").read().strip())
    print("clk_rate", open("/sys/kernel/debug/clk/cclk_sdmmc0/clk_rate").read().strip())
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    sd = mmap.mmap(fd, 0x4000, offset=SD)

    def rd(o):
        return struct.unpack_from("<I", sd, o)[0]

    def wr(o, v):
        struct.pack_into("<I", sd, o, v)

    def wait():
        t0 = time.time()
        while time.time() - t0 < 0.2:
            if (rd(CMD) & CMD_START) == 0:
                return True
            time.sleep(0.0004)
        return False

    def cmd(op, arg, flags, delay=0.008):
        wr(RINTSTS, 0xFFFFFFFF)
        wr(CMDARG, arg)
        wr(CMD, CMD_START | CMD_WAIT | flags | op)
        ok = wait()
        time.sleep(delay)
        st, resp = rd(RINTSTS), rd(RESP0)
        print("CMD%-2d arg=%08x rint=%08x resp=%08x" % (op, arg, st, resp))
        return resp, st

    cmd(0, 0, CMD_INIT, 0.03)
    r7 = 0
    for i in range(8):
        r7, st = cmd(8, 0x1AA, CMD_RESP | CMD_CRC)
        if (r7 & 0xFF) == 0xAA:
            print("CMD8_OK try", i)
            break
    else:
        print("CMD8_FAIL")
        sd.close()
        os.close(fd)
        return
    ocr = 0
    for i in range(50):
        cmd(55, 0, CMD_RESP | CMD_CRC, 0.003)
        ocr, st = cmd(41, 0x40FF8000, CMD_RESP, 0.01)
        if ocr & 0x80000000:
            print("READY ocr=%08x CCS=%d" % (ocr, 1 if (ocr & 0x40000000) else 0))
            break
    # CID
    cmd(2, 0, CMD_RESP | (1 << 7), 0.01)  # 136-bit: bit7 = long resp if this controller uses it
    print("RESP0123", hex(rd(0x30)), hex(rd(0x34)), hex(rd(0x38)), hex(rd(0x3C)))
    sd.close()
    os.close(fd)


if __name__ == "__main__":
    main()
