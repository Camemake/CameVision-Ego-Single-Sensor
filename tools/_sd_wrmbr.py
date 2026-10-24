#!/usr/bin/env python3
import os
import struct

os.system("umount /mnt/sdcard 2>/dev/null")
print("size", open("/sys/block/mmcblk1/size").read().strip())
fd = os.open("/dev/mmcblk1", os.O_RDWR)
before = os.read(fd, 512)
print("before type", before[0x1BE + 4], "start", struct.unpack_from("<I", before, 0x1BE + 8))
mbr = bytearray(512)
mbr[0x1BE + 4] = 0x0C
struct.pack_into("<I", mbr, 0x1BE + 8, 32)
struct.pack_into("<I", mbr, 0x1BE + 12, 30535648)
mbr[510] = 0x55
mbr[511] = 0xAA
os.lseek(fd, 0, os.SEEK_SET)
n = os.write(fd, mbr)
print("wrote", n)
os.fsync(fd)
os.lseek(fd, 0, os.SEEK_SET)
after = os.read(fd, 512)
os.close(fd)
print(
    "after type",
    after[0x1BE + 4],
    "start",
    struct.unpack_from("<I", after, 0x1BE + 8),
    "nsect",
    struct.unpack_from("<I", after, 0x1BE + 12),
    "sig",
    after[510:512].hex(),
)
os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
fd = os.open("/dev/mmcblk1", os.O_RDONLY)
os.lseek(fd, 0, os.SEEK_SET)
again = os.read(fd, 512)
os.close(fd)
print(
    "reread type",
    again[0x1BE + 4],
    "start",
    struct.unpack_from("<I", again, 0x1BE + 8),
)
