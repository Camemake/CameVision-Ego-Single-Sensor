#!/usr/bin/env python3
"""Partition + FAT32 the SD to the Windows 16 GB layout (LBA 32, type 0x0C)."""
import os
import struct
import time

DEV = "/dev/mmcblk1"
START = 32
TOTAL = 30535680
NSECT = TOTAL - START


def main():
    os.system("umount /mnt/sdcard 2>/dev/null")
    size = int(open("/sys/block/mmcblk1/size").read().strip())
    print("size", size)
    if size < 30000000:
        print("CAPACITY_TOO_SMALL")
        return 2
    fd = os.open(DEV, os.O_RDWR)
    mbr = bytearray(512)
    mbr[0x1BE + 4] = 0x0C
    struct.pack_into("<I", mbr, 0x1BE + 8, START)
    struct.pack_into("<I", mbr, 0x1BE + 12, NSECT)
    mbr[510] = 0x55
    mbr[511] = 0xAA
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, mbr)
    os.fsync(fd)
    os.close(fd)
    print("MBR_OK start", START, "nsect", NSECT)
    os.system("blockdev --rereadpt /dev/mmcblk1 2>/dev/null")
    os.system("echo 1 > /sys/block/mmcblk1/device/rescan 2>/dev/null")
    time.sleep(1)
    if not os.path.exists("/dev/mmcblk1p1"):
        print("NO_P1")
        return 3
    rc = os.system("mkfs.vfat -F 32 -n CAMEVISION /dev/mmcblk1p1")
    print("mkfs", rc)
    if rc != 0:
        return 4
    os.makedirs("/mnt/sdcard", exist_ok=True)
    rc = os.system("mount -t vfat -o utf8,flush /dev/mmcblk1p1 /mnt/sdcard")
    print("mount", rc)
    os.system("df -h /mnt/sdcard")
    os.system("ls /mnt/sdcard")
    return 0 if rc == 0 else 5


if __name__ == "__main__":
    raise SystemExit(main())
