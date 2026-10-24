#!/usr/bin/env python3
"""After SD 2.0 init, read LBA 0 and 32 as block addresses (CCS=0 card)."""
import mmap
import os
import struct
import time

SD = 0x21D60000
CMDARG, CMD, RESP0, RINTSTS = 0x28, 0x2C, 0x30, 0x44
BMOD, PLDMND = 0x80, 0x84
CMD_START, CMD_WAIT, CMD_INIT = 1 << 31, 1 << 13, 1 << 15
CMD_CRC, CMD_RESP, CMD_DATA = 1 << 8, 1 << 6, 1 << 9
CMD_READ = 1 << 10  # DW_MCI_CMD_DAT_EXP + read? check
# Synopsys: bit 9 = data expected, bit 10 = write (1=write, 0=read)


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
        while time.time() - t0 < 0.25:
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
        print("CMD%-2d arg=%08x rint=%08x resp=%08x" % (op, arg, rd(RINTSTS), rd(RESP0)))
        return rd(RESP0)

    cmd(0, 0, CMD_INIT, 0.03)
    for _ in range(4):
        r = cmd(8, 0x1AA, CMD_RESP | CMD_CRC)
        if (r & 0xFF) == 0xAA:
            print("CMD8_OK")
            break
    for _ in range(40):
        cmd(55, 0, CMD_RESP | CMD_CRC, 0.003)
        ocr = cmd(41, 0x40FF8000, CMD_RESP, 0.01)
        if ocr & 0x80000000:
            print("READY ocr=%08x CCS=%d" % (ocr, 1 if (ocr & 0x40000000) else 0))
            break
    cmd(2, 0, CMD_RESP | (1 << 7))
    rca = cmd(3, 0, CMD_RESP | CMD_CRC)
    rca &= 0xFFFF0000
    print("RCA", hex(rca))
    # CSD
    cmd(9, rca, CMD_RESP | (1 << 7))
    print("CSD", hex(rd(0x30)), hex(rd(0x34)), hex(rd(0x38)), hex(rd(0x3C)))
    cmd(7, rca, CMD_RESP | CMD_CRC)
    cmd(16, 512, CMD_RESP | CMD_CRC)
    print("done select, leaving host for driver")
    sd.close()
    os.close(fd)


if __name__ == "__main__":
    main()
