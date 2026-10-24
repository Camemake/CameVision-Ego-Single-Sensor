#!/usr/bin/env python3
import os

dev = "/dev/mmcblk1p1"
boot = open(dev, "rb").read(512)
print(
    "before",
    boot[19] + 256 * boot[20],
    boot[32] + (boot[33] << 8) + (boot[34] << 16) + (boot[35] << 24),
    boot[43:54],
)
b = bytearray(boot)
b[19] = 0
b[20] = 0
n = 30535680
b[32] = n & 255
b[33] = (n >> 8) & 255
b[34] = (n >> 16) & 255
b[35] = (n >> 24) & 255
label = b"CAMEVISION"
b[43:54] = label + b" " * (11 - len(label))
b[510] = 0x55
b[511] = 0xAA
fd = os.open(dev, os.O_WRONLY)
os.lseek(fd, 0, os.SEEK_SET)
os.write(fd, bytes(b))
os.fsync(fd)
os.close(fd)
boot = open(dev, "rb").read(512)
total = boot[32] + (boot[33] << 8) + (boot[34] << 16) + (boot[35] << 24)
print("after", boot[19] + 256 * boot[20], total, boot[43:54], total * 512)
