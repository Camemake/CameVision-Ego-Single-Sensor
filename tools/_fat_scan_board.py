#!/usr/bin/env python3
import os
import struct

fd = os.open("/dev/mmcblk1p1", os.O_RDONLY)
bs = os.read(fd, 512)
bps = struct.unpack_from("<H", bs, 11)[0]
res = struct.unpack_from("<H", bs, 14)[0]
nf = bs[16]
root = struct.unpack_from("<H", bs, 17)[0]
fz = struct.unpack_from("<H", bs, 22)[0]
off = (res + nf * fz) * bps
os.lseek(fd, off, 0)
data = os.read(fd, root * 32)
os.close(fd)
print("root_bytes", len(data), "ents", root)
hits = 0
for i in range(0, len(data), 32):
    e = data[i : i + 32]
    if not e or e[0] == 0:
        continue
    name = e[:11]
    print(
        "ENT",
        i // 32,
        name,
        hex(e[11]),
        struct.unpack_from("<H", e, 26)[0],
        struct.unpack_from("<I", e, 28)[0],
    )
    hits += 1
print("hits", hits)
