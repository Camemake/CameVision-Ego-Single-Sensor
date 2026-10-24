#!/usr/bin/env python3
"""Force CMD8=0x1AA and retry it after extra CMD0s, then rebind mmc1."""
import mmap
import os
import struct
import time

PHYS = 0x40200000
OFF_BL = 0x5A7568          # bl mmc_send_if_cond
OFF_ARG = 0x5A879C         # mov w2,#0xaa ; orr w1,w1,w2
OFF_CAVE = 0x5B73EC        # execute_tuning
SEND_IF = 0x5A89F8
GO_IDLE = 0x5A58D0

# bl cave from get_cid
BL_CAVE = struct.pack("<I", 0x94000000 | (((OFF_CAVE - OFF_BL) // 4) & 0x3FFFFFF))
# original bl send_if_cond
BL_ORIG = bytes.fromhex("24050094")
FORCE_1AA = struct.pack("<II", 0x52803541, 0xD503201F)  # mov w1,#0x1aa; nop
ORIG_ARG = bytes.fromhex("421580522100022a")


def bl_to(src, dst):
    return 0x94000000 | (((dst - src) // 4) & 0x3FFFFFF)


def map_off(fd, off, n=64):
    phys = PHYS + off
    page = phys & ~0xFFF
    rel = phys - page
    return mmap.mmap(fd, rel + n, offset=page), rel


def main():
    # cave at execute_tuning
    # stp x29,x30,[sp,#-0x20]!
    # stp x21,xzr,[sp,#16]
    # mov x29,sp
    # mov w21,#12
    # 1: mov x0,x19
    #    bl go_idle
    #    mov x0,x19
    #    mov w1,w20
    #    bl send_if_cond
    #    cbz w0, 2
    #    subs w21,w21,#1
    #    b.ne 1
    # 2: ldp x21,xzr,[sp,#16]
    #    ldp x29,x30,[sp],#0x20
    #    ret
    ins = []
    cave = OFF_CAVE
    ins.append(0xA9BE7BFD)          # stp x29,x30,[sp,#-0x20]!
    ins.append(0xA9017FF5)          # stp x21,xzr,[sp,#16]
    ins.append(0x910003FD)          # mov x29,sp
    ins.append(0x52800195)          # mov w21,#12
    loop = cave + 16
    ins.append(0xAA1303E0)          # mov x0,x19
    ins.append(bl_to(loop + 4, GO_IDLE))
    ins.append(0xAA1303E0)          # mov x0,x19
    ins.append(0x2A1403E1)          # mov w1,w20
    ins.append(bl_to(loop + 16, SEND_IF))
    ins.append(0x34000060)          # cbz w0, +12 (to epilogue)
    ins.append(0x710006B5)          # subs w21,w21,#1
    ins.append(0x54FFFF41)          # b.ne loop  (back 6 insns from here: here=loop+24, loop is -6)
    # wait: b.ne target
    # this insn at loop+20? Let's count.
    # I'll fix branches after building with addresses.

    # rebuild with known addresses
    words = [
        (cave + 0, 0xA9BE7BFD),
        (cave + 4, 0xA9017FF5),
        (cave + 8, 0x910003FD),
        (cave + 12, 0x52800195),
        (cave + 16, 0xAA1303E0),
        (cave + 20, bl_to(cave + 20, GO_IDLE)),
        (cave + 24, 0xAA1303E0),
        (cave + 28, 0x2A1403E1),
        (cave + 32, bl_to(cave + 32, SEND_IF)),
        (cave + 36, 0x34000080),  # cbz w0, +4 insns -> epilogue at +52? 
        (cave + 40, 0x710006B5),
        (cave + 44, 0),  # b.ne loop
        (cave + 48, 0xA9417FF5),  # epilogue ldp x21,xzr
        (cave + 52, 0xA8C27BFD),  # ldp x29,x30,[sp],#0x20
        (cave + 56, 0xD65F03C0),  # ret
    ]
    # cbz w0 from +36 to +48: +12 bytes = 3 insns, imm19=3 → 0x34000060
    words[9] = (cave + 36, 0x34000060)
    # b.ne from +44 to +16: -28 bytes = -7 insns
    words[11] = (cave + 44, 0x54FFFF21)  # imm19=-7, cond=1 (ne)
    # 0x54FFFFE1 is -1; -7 = 0x54FFFF21? imm19 in bits 23:5
    # 54 | (imm19<<5) | 1
    # imm19 = -7 & 0x7FFFF = 0x7FFF9
    # 0x54000001 | (0x7FFF9 << 5) = 0x54000001 | 0xFFFF20 = 0x54FFFF21
    blob = b"".join(struct.pack("<I", w) for _, w in words)

    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    m, rel = map_off(fd, OFF_CAVE, 64)
    m[rel : rel + len(blob)] = blob
    print("cave", m[rel : rel + 16].hex())
    m.close()

    m, rel = map_off(fd, OFF_BL, 8)
    print("bl", m[rel : rel + 4].hex(), "->", BL_CAVE.hex())
    m[rel : rel + 4] = BL_CAVE
    m.close()

    m, rel = map_off(fd, OFF_ARG, 8)
    print("arg", m[rel : rel + 8].hex())
    m[rel : rel + 8] = FORCE_1AA
    print("arg now", m[rel : rel + 8].hex())
    m.close()
    os.close(fd)

    os.system("umount /mnt/sdcard 2>/dev/null")
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind")
    time.sleep(1)
    os.system("echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind")
    time.sleep(4)
    os.system("dmesg | grep -E 'mmc1|21d60000' | tail -15")
    os.system(
        "p=$(ls -d /sys/class/mmc_host/mmc1/mmc1:* 2>/dev/null | head -1); "
        "echo P=$p; "
        "echo TYPE=$(cat $p/type 2>/dev/null); "
        "echo OCR=$(cat $p/ocr 2>/dev/null); "
        "echo CSD=$(cat $p/csd 2>/dev/null); "
        "echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)"
    )


if __name__ == "__main__":
    main()
