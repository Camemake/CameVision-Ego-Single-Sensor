#!/usr/bin/env python3
import os

print("ro", open("/sys/block/mmcblk1/ro").read().strip())
print("size", open("/sys/block/mmcblk1/size").read().strip())
os.system("dmesg | tail -8")
rc = os.system("dd if=/dev/zero of=/dev/mmcblk1 bs=512 count=1 conv=fsync")
print("dd", rc)
open("/proc/sys/vm/drop_caches", "w").write("3\n")
fd = os.open("/dev/mmcblk1", os.O_RDONLY)
data = os.read(fd, 32)
os.close(fd)
print("first32", data.hex())
os.system("dmesg | tail -12")
