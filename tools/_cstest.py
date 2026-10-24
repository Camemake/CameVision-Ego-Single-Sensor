#!/usr/bin/env python3
"""Fresh FunctionFS write: working video ifaces PLUS one CS_INTERFACE."""
import os
import struct

def u16(n):
    return struct.pack("<H", n)

def u32(n):
    return struct.pack("<I", n)

def n_desc(blob):
    i = n = 0
    while i < len(blob):
        ln = blob[i]
        n += 1
        i += ln
    return n

def video(maxpkt, with_cs=True):
    iad = bytes([8, 11, 0, 2, 14, 2, 0, 1])
    vc = bytes([9, 4, 0, 0, 0, 14, 1, 0, 1])
    # Minimal VC header only (CS_INTERFACE)
    cs = bytes([13, 0x24, 1, 0x00, 0x01]) + u16(13) + u32(48000000) + bytes([1, 1])
    vs0 = bytes([9, 4, 1, 0, 0, 14, 2, 0, 1])
    vs1 = bytes([9, 4, 1, 1, 1, 14, 2, 0, 0])
    ep = bytes([7, 5, 0x81, 2]) + u16(maxpkt) + bytes([0])
    if with_cs:
        return iad + vc + cs + vs0 + vs1 + ep
    return iad + vc + vs0 + vs1 + ep

def try_write(name, fs, hs):
    os.system("umount /dev/usb-ffs/uvc 2>/dev/null")
    os.system("mkdir -p /dev/usb-ffs/uvc")
    os.system("mount -o uid=0,gid=0 -t functionfs uvc /dev/usb-ffs/uvc")
    fd = os.open("/dev/usb-ffs/uvc/ep0", os.O_RDWR)
    body = fs + hs
    blob = u32(3) + u32(20 + len(body)) + u32(3) + u32(n_desc(fs)) + u32(n_desc(hs)) + body
    try:
        os.write(fd, blob)
        print("OK", name, "fs", n_desc(fs), "len", len(blob))
        raw = b"Camemake\x00"
        slen = 16 + 2 + len(raw)
        os.write(fd, u32(2) + u32(slen) + u32(1) + u32(1) + u16(0x0409) + raw)
        print("STRINGS_OK", name)
        os.close(fd)
        return True
    except OSError as e:
        print("FAIL", name, e)
        os.close(fd)
        return False

def main():
    print("no-cs")
    try_write("no-cs", video(64, False), video(512, False))
    print("with-cs")
    try_write("with-cs", video(64, True), video(512, True))

if __name__ == "__main__":
    main()
