#!/usr/bin/env python3
"""FunctionFS UVC gadget. Avoids f_uvc (gadget_start -19 on this dwc3).

Bulk MJPEG 1400x1600 named Camemake. JPEG still comes from single_live.
"""
from __future__ import annotations

import os
import select
import struct
import time

EP0 = "/dev/usb-ffs/uvc/ep0"
EP1 = "/dev/usb-ffs/uvc/ep1"
LIVE = "/tmp/camevision-live.jpg"
LOG = "/userdata/cv-ffs-uvc.log"
W, H = 1400, 1600

FUNCTIONFS_DESCRIPTORS_MAGIC_V2 = 3
FUNCTIONFS_STRINGS_MAGIC = 2
FUNCTIONFS_HAS_FS_DESC = 1
FUNCTIONFS_HAS_HS_DESC = 2
FUNCTIONFS_BIND, FUNCTIONFS_UNBIND = 0, 1
FUNCTIONFS_ENABLE, FUNCTIONFS_DISABLE = 2, 3
FUNCTIONFS_SETUP, FUNCTIONFS_SUSPEND, FUNCTIONFS_RESUME = 4, 5, 6

UVC_SET_CUR, UVC_GET_CUR = 0x01, 0x81
UVC_GET_MIN, UVC_GET_MAX = 0x82, 0x83
UVC_GET_RES, UVC_GET_LEN = 0x84, 0x85
UVC_GET_INFO, UVC_GET_DEF = 0x86, 0x87
UVC_VS_PROBE, UVC_VS_COMMIT = 0x01, 0x02


def log(msg: str) -> None:
    with open(LOG, "a") as fh:
        fh.write(msg + "\n")


def u16(n: int) -> bytes:
    return struct.pack("<H", n)


def u32(n: int) -> bytes:
    return struct.pack("<I", n)


def pack_probe(interval: int = 333333) -> bytes:
    return struct.pack(
        "<HBBIHHHHHIII BBBB",
        0, 1, 1, interval, 0, 0, 0, 0, 0,
        W * H * 2, 1024, 48000000, 0, 1, 1, 1,
    )


def build_uvc_descs(maxpkt: int) -> bytes:
    iad = bytes([8, 11, 0, 2, 14, 2, 0, 4])
    vc_if = bytes([9, 4, 0, 0, 0, 14, 1, 0, 5])
    cam = bytes([
        18, 0x24, 2, 1, 0x01, 0x02, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0x2A, 0, 0,
    ])
    proc = bytes([11, 0x24, 5, 2, 1, 0, 0, 2, 0x2F, 0x13, 0])
    out = bytes([9, 0x24, 3, 3, 0x01, 0x01, 1, 2, 0])
    vc_body = cam + proc + out
    vc_hdr = bytes([13, 0x24, 1, 0x00, 0x01]) + u16(13 + len(vc_body)) + u32(48000000) + bytes([1, 1])
    vs0 = bytes([9, 4, 1, 0, 0, 14, 2, 0, 6])
    mjpeg = bytes([11, 0x24, 6, 1, 1, 0, 1, 0, 0, 0, 0])
    frame = bytes([30, 0x24, 7, 1, 0]) + u16(W) + u16(H)
    frame += u32(W * H * 16 * 5) + u32(W * H * 16 * 30) + u32(W * H * 2)
    frame += u32(333333) + bytes([1]) + u32(333333)
    color = bytes([6, 0x24, 13, 1, 1, 4])
    vs_body = mjpeg + frame + color
    # input header: 13 + p + n bytes; p=1 format, bEndpointAddress 0x81
    vs_hdr = bytes([14, 0x24, 1, 1]) + u16(14 + len(vs_body)) + bytes([0x81, 0, 0, 0, 1, 0, 0, 0])
    vs1 = bytes([9, 4, 1, 1, 1, 14, 2, 0, 0])
    ep = bytes([7, 5, 0x81, 2]) + u16(maxpkt) + bytes([0])
    return iad + vc_if + vc_hdr + vc_body + vs0 + vs_hdr + vs_body + vs1 + ep


def build_uvc_descs_noiad(maxpkt: int) -> bytes:
    return build_uvc_descs(maxpkt)[8:]


def n_desc(blob: bytes) -> int:
    i = n = 0
    while i < len(blob):
        ln = blob[i]
        if ln < 2:
            raise ValueError("bad desc at %d" % i)
        n += 1
        i += ln
    if i != len(blob):
        raise ValueError("desc tail %d/%d" % (i, len(blob)))
    return n


def build_min_descs(maxpkt: int) -> bytes:
    iface = bytes([9, 4, 0, 0, 1, 0xFF, 0, 0, 4])
    ep = bytes([7, 5, 0x81, 2]) + u16(maxpkt) + bytes([0])
    return iface + ep


def build_video_ifaces(maxpkt: int) -> bytes:
    # Standard USB descriptors only (this FunctionFS rejects CS_INTERFACE 0x24).
    iad = bytes([8, 11, 0, 2, 14, 2, 0, 1])
    vc = bytes([9, 4, 0, 0, 0, 14, 1, 0, 1])
    vs0 = bytes([9, 4, 1, 0, 0, 14, 2, 0, 1])
    vs1 = bytes([9, 4, 1, 1, 1, 14, 2, 0, 0])
    ep = bytes([7, 5, 0x81, 2]) + u16(maxpkt) + bytes([0])
    return iad + vc + vs0 + vs1 + ep


def write_descs(fd: int) -> None:
    fs = build_video_ifaces(64)
    hs = build_video_ifaces(512)
    nfs, nhs = n_desc(fs), n_desc(hs)
    body = fs + hs
    blob = u32(FUNCTIONFS_DESCRIPTORS_MAGIC_V2) + u32(20 + len(body)) + u32(3) + u32(nfs) + u32(nhs) + body
    os.write(fd, blob)
    log("descs video-ifaces ok fs=%d hs=%d" % (nfs, nhs))
    raw = b"Camemake\x00"
    slen = 16 + 2 + len(raw)
    sblob = u32(FUNCTIONFS_STRINGS_MAGIC) + u32(slen) + u32(1) + u32(1) + u16(0x0409) + raw
    os.write(fd, sblob)
    log("DESCS_OK video-ifaces")


def read_live() -> bytes:
    try:
        data = open(LIVE, "rb").read()
    except OSError:
        return b""
    if len(data) < 200 or data[:2] != b"\xff\xd8":
        return b""
    return data


def uvc_header(fid: int, eof: int) -> bytes:
    return bytes([2, (fid & 1) | ((eof & 1) << 1)])


def main() -> int:
    os.makedirs("/dev/usb-ffs/uvc", exist_ok=True)
    fd0 = os.open(EP0, os.O_RDWR)
    write_descs(fd0)
    probe = pack_probe()
    commit = probe
    enabled = False
    streaming = False
    fid = 0
    ep1 = -1
    log("waiting events")
    while True:
        r, _, _ = select.select([fd0], [], [], 0.02)
        if r:
            ev = os.read(fd0, 12)
            if len(ev) < 12:
                continue
            typ = ev[8]
            if typ == FUNCTIONFS_BIND:
                log("BIND")
            elif typ == FUNCTIONFS_UNBIND:
                log("UNBIND")
                streaming = False
            elif typ == FUNCTIONFS_ENABLE:
                log("ENABLE")
                enabled = True
                if ep1 < 0:
                    try:
                        ep1 = os.open(EP1, os.O_WRONLY)
                    except OSError as exc:
                        log("ep1 %s" % exc)
            elif typ == FUNCTIONFS_DISABLE:
                log("DISABLE")
                enabled = False
                streaming = False
            elif typ == FUNCTIONFS_SETUP:
                bm, req = ev[0], ev[1]
                wvalue = ev[2] | (ev[3] << 8)
                windex = ev[4] | (ev[5] << 8)
                wlen = ev[6] | (ev[7] << 8)
                is_in = (bm & 0x80) != 0
                iface = windex & 0xFF
                cs = (wvalue >> 8) & 0xFF
                log("SETUP bm=0x%x req=0x%x iface=%d cs=0x%x len=%d" % (bm, req, iface, cs, wlen))
                if req == 11 and not is_in:  # SET_INTERFACE
                    alt = wvalue
                    streaming = enabled and alt == 1
                    log("SET_INTERFACE alt=%d stream=%s" % (alt, streaming))
                    if wlen:
                        try:
                            os.read(fd0, wlen)
                        except OSError:
                            pass
                    continue
                data = b""
                if iface == 1 and cs in (UVC_VS_PROBE, UVC_VS_COMMIT):
                    if is_in and req in (UVC_GET_CUR, UVC_GET_MIN, UVC_GET_MAX, UVC_GET_DEF):
                        data = probe if cs == UVC_VS_PROBE else commit
                    elif is_in and req == UVC_GET_LEN:
                        data = struct.pack("<H", 34)
                    elif is_in and req == UVC_GET_INFO:
                        data = b"\x03"
                    elif (not is_in) and req == UVC_SET_CUR:
                        try:
                            payload = os.read(fd0, wlen)
                        except OSError:
                            payload = b""
                        if len(payload) >= 8:
                            got = struct.unpack_from("<I", payload, 4)[0]
                            interval = got if got in (333333, 666666, 1000000, 2000000) else 333333
                            probe = pack_probe(interval)
                            if cs == UVC_VS_COMMIT:
                                commit = probe
                            log("SET probe/commit interval=%d" % interval)
                        continue
                elif is_in and req == UVC_GET_INFO:
                    data = b"\x03"
                elif is_in and req == UVC_GET_LEN:
                    data = struct.pack("<H", 2)
                elif is_in:
                    data = b"\x00" * min(wlen, 34)
                elif wlen:
                    try:
                        os.read(fd0, wlen)
                    except OSError:
                        pass
                    continue
                if is_in:
                    try:
                        os.write(fd0, data[:wlen] if wlen else data)
                    except OSError as exc:
                        log("ep0 write %s" % exc)
            else:
                log("event %d" % typ)
        if streaming and ep1 >= 0:
            jpg = read_live()
            if jpg:
                try:
                    os.write(ep1, uvc_header(fid, 0) + jpg[:-1])
                    os.write(ep1, uvc_header(fid, 1) + jpg[-1:])
                    fid ^= 1
                except OSError as exc:
                    if exc.errno not in (11, 32, 108):
                        log("ep1 %s" % exc)
                    time.sleep(0.01)
            else:
                time.sleep(0.02)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
