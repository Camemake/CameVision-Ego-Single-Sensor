#!/usr/bin/env python3
"""UVC gadget pump. Image stays on Rockchip; this only answers the host.

Linux-UVC- model: subscribe gadget events, STREAMON only when the host
asks, keep a latest JPEG, recycle output buffers. JPEG comes from
single_live (/tmp/camevision-live.jpg) so exposure/AWB/color stay here.
"""
from __future__ import annotations

import ctypes
import fcntl
import mmap
import os
import select
import signal
import struct
import time

AM = os.path.isfile("/userdata/camevision-am.on")
if AM:
    W, H = 1400, 1600
else:
    W, H = 1920, 1200
MAX_FRAME = W * H * 3 // 2
LIVE_JPG = "/tmp/camevision-live.jpg"
LOG = "/userdata/cv-uvc-bridge.log"

V4L2_BUF_TYPE_VIDEO_OUTPUT = 2
V4L2_MEMORY_MMAP = 1
V4L2_PIX_FMT_MJPG = 0x47504A4D
V4L2_EVENT_PRIVATE_START = 0x08000000
UVC_EVENT_CONNECT = V4L2_EVENT_PRIVATE_START + 0
UVC_EVENT_DISCONNECT = V4L2_EVENT_PRIVATE_START + 1
UVC_EVENT_STREAMON = V4L2_EVENT_PRIVATE_START + 2
UVC_EVENT_STREAMOFF = V4L2_EVENT_PRIVATE_START + 3
UVC_EVENT_SETUP = V4L2_EVENT_PRIVATE_START + 4
UVC_EVENT_DATA = V4L2_EVENT_PRIVATE_START + 5

UVC_SET_CUR = 0x01
UVC_GET_CUR = 0x81
UVC_GET_MIN = 0x82
UVC_GET_MAX = 0x83
UVC_GET_RES = 0x84
UVC_GET_LEN = 0x85
UVC_GET_INFO = 0x86
UVC_GET_DEF = 0x87
UVC_VS_PROBE = 0x01
UVC_VS_COMMIT = 0x02
UVC_RC_NO_ERROR = 0x00
UVC_RC_INVALID_CONTROL = 0x06

# Linux 6.1 g_uvc.h: _IOW('U', 1, struct uvc_request_data)
UVCIOC_SEND_RESPONSE = (1 << 30) | (ord("U") << 8) | 1 | (64 << 16)


def _ioc(dir_, typ, nr, size):
    return (dir_ << 30) | (ord(typ) << 8) | nr | (size << 16)


VIDIOC_S_FMT = _ioc(3, "V", 5, 208)
VIDIOC_REQBUFS = _ioc(3, "V", 8, 20)
VIDIOC_QUERYBUF = _ioc(3, "V", 9, 88)
VIDIOC_QBUF = _ioc(3, "V", 15, 88)
VIDIOC_DQBUF = _ioc(3, "V", 17, 88)
VIDIOC_STREAMON = _ioc(1, "V", 18, 4)
VIDIOC_STREAMOFF = _ioc(1, "V", 19, 4)
# sizes are probed against this kernel; 32 is v4l2_event_subscription


class v4l2_requestbuffers(ctypes.Structure):
    _fields_ = [
        ("count", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("memory", ctypes.c_uint32),
        ("capabilities", ctypes.c_uint32),
        ("flags", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
    ]


class timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_int64), ("tv_usec", ctypes.c_int64)]


class v4l2_timecode(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("frames", ctypes.c_uint8),
        ("seconds", ctypes.c_uint8),
        ("minutes", ctypes.c_uint8),
        ("hours", ctypes.c_uint8),
        ("userbits", ctypes.c_uint8 * 4),
    ]


class v4l2_buffer(ctypes.Structure):
    class _m(ctypes.Union):
        _fields_ = [
            ("offset", ctypes.c_uint32),
            ("userptr", ctypes.c_ulong),
            ("planes", ctypes.c_void_p),
            ("fd", ctypes.c_int32),
        ]

    _fields_ = [
        ("index", ctypes.c_uint32),
        ("type", ctypes.c_uint32),
        ("bytesused", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("field", ctypes.c_uint32),
        ("timestamp", timeval),
        ("timecode", v4l2_timecode),
        ("sequence", ctypes.c_uint32),
        ("memory", ctypes.c_uint32),
        ("m", _m),
        ("length", ctypes.c_uint32),
        ("reserved2", ctypes.c_uint32),
        ("request_fd", ctypes.c_int32),
    ]


def log(msg: str) -> None:
    with open(LOG, "a") as fh:
        fh.write(msg + "\n")


def find_uvc() -> str:
    skip = ("rkisp", "rkcif", "rkvpss", "rkfec", "rkaiisp", "stream_cif", "statistics")
    hits = []
    for ent in sorted(os.listdir("/sys/class/video4linux")):
        if not ent.startswith("video"):
            continue
        try:
            name = open("/sys/class/video4linux/%s/name" % ent).read().strip()
        except OSError:
            continue
        low = name.lower()
        if any(s in low for s in skip):
            continue
        if any(s in low for s in ("gadget", "uvc", "camevision", "dummy_udc", "f_uvc")):
            hits.append(("/dev/" + ent, name))
    if hits:
        log("uvc node %s (%s)" % (hits[0][0], hits[0][1]))
        return hits[0][0]
    raise OSError("no UVC gadget video node")


def read_live_jpeg() -> bytes:
    try:
        data = open(LIVE_JPG, "rb").read()
    except OSError:
        return b""
    if len(data) < 200 or data[:2] != b"\xff\xd8":
        return b""
    return data


def pack_probe(interval: int = 333333) -> bytes:
    # struct uvc_streaming_control, 34 bytes
    return struct.pack(
        "<HBBIHHHHHIII BBBB",
        0,  # bmHint
        1,  # bFormatIndex MJPEG
        1,  # bFrameIndex
        interval,
        0,
        0,
        0,
        0,
        0,
        MAX_FRAME,
        1024,
        48000000,
        0,
        1,
        1,
        1,
    )


class UvcOut:
    def __init__(self, dev: str) -> None:
        self.fd = os.open(dev, os.O_RDWR | os.O_NONBLOCK)
        self.maps: list[tuple[mmap.mmap, int]] = []
        self.nbuf = 0
        self.queued = 0
        self.streaming = False
        self.events = False
        self.dqevent_size = 136
        self.pending_out = 0
        self.prepared = False
        self.probe = pack_probe()
        self.commit = self.probe
        self.err = UVC_RC_NO_ERROR

    def setup(self) -> None:
        raw = bytearray(208)
        struct.pack_into("<I", raw, 0, V4L2_BUF_TYPE_VIDEO_OUTPUT)
        struct.pack_into("<IIIIII", raw, 8, W, H, V4L2_PIX_FMT_MJPG, 1, 0, 0)
        struct.pack_into("<I", raw, 32, MAX_FRAME)
        fcntl.ioctl(self.fd, VIDIOC_S_FMT, raw)
        req = v4l2_requestbuffers()
        req.count = 4
        req.type = V4L2_BUF_TYPE_VIDEO_OUTPUT
        req.memory = V4L2_MEMORY_MMAP
        fcntl.ioctl(self.fd, VIDIOC_REQBUFS, req)
        self.nbuf = int(req.count)
        if self.nbuf < 2:
            raise OSError("reqbufs %d" % self.nbuf)
        for i in range(self.nbuf):
            buf = v4l2_buffer()
            buf.type = V4L2_BUF_TYPE_VIDEO_OUTPUT
            buf.memory = V4L2_MEMORY_MMAP
            buf.index = i
            fcntl.ioctl(self.fd, VIDIOC_QUERYBUF, buf)
            mm = mmap.mmap(
                self.fd,
                buf.length,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=buf.m.offset,
            )
            self.maps.append((mm, buf.length))
        log("uvc mmap %d x %d %dx%d" % (self.nbuf, self.maps[0][1], W, H))
        self._subscribe()

    def _subscribe(self) -> None:
        ok = False
        events = [
            UVC_EVENT_CONNECT,
            UVC_EVENT_DISCONNECT,
            UVC_EVENT_STREAMON,
            UVC_EVENT_STREAMOFF,
            UVC_EVENT_SETUP,
            UVC_EVENT_DATA,
            UVC_EVENT_STREAMON + 4,  # SUSPEND on Rockchip
            UVC_EVENT_STREAMON + 5,  # RESUME
        ]
        for size in (32, 64):
            cmd = _ioc(1, "V", 90, size)
            size_ok = False
            for ev in events:
                sub = bytearray(size)
                struct.pack_into("<I", sub, 0, ev)
                try:
                    fcntl.ioctl(self.fd, cmd, sub)
                    size_ok = True
                    ok = True
                except OSError as exc:
                    log("subscribe 0x%x size=%d %s" % (ev, size, exc))
            if size_ok:
                log("subscribe size=%d" % size)
                break
        self.events = ok
        log("subscribed UVC events" if ok else "no UVC events — pump MJPEG")

    def send_response(self, data: bytes | None, length: int | None = None) -> None:
        blob = bytearray(64)
        if data is None and length is None:
            struct.pack_into("<i", blob, 0, 0)
        elif data is None:
            struct.pack_into("<i", blob, 0, int(length or 0))
        else:
            struct.pack_into("<i", blob, 0, min(len(data), 60))
            blob[4 : 4 + min(len(data), 60)] = data[:60]
        fcntl.ioctl(self.fd, UVCIOC_SEND_RESPONSE, blob)

    def stall(self) -> None:
        blob = bytearray(64)
        struct.pack_into("<i", blob, 0, -132)  # -EL2HLT
        try:
            fcntl.ioctl(self.fd, UVCIOC_SEND_RESPONSE, blob)
        except OSError as exc:
            log("stall %s" % exc)
        self.err = UVC_RC_INVALID_CONTROL

    def handle_event(self) -> None:
        last_exc = None
        raw = None
        for size in (self.dqevent_size, 136, 144, 168, 192, 256, 128, 160):
            blob = bytearray(size)
            for dir_ in (2, 3):
                cmd = _ioc(dir_, "V", 89, size)
                try:
                    fcntl.ioctl(self.fd, cmd, blob)
                    self.dqevent_size = size
                    raw = blob
                    break
                except OSError as exc:
                    last_exc = exc
                    if exc.errno == 2:
                        return
                    if exc.errno not in (25, 22):
                        raise
            if raw is not None:
                break
        if raw is None:
            raise last_exc or OSError("DQEVENT")
        ev = struct.unpack_from("<I", raw, 0)[0]
        # v4l2_event.u is 8-byte aligned: type(4)+pad(4)+data[64]
        data = raw[8:72] if len(raw) >= 72 else raw[4:68]
        if ev == UVC_EVENT_SETUP:
            self._setup(data)
        elif ev == UVC_EVENT_DATA:
            self._data(data)
        elif ev == UVC_EVENT_STREAMON:
            self.ensure_stream()
        elif ev == UVC_EVENT_STREAMOFF:
            self.stop_stream()
        elif ev == UVC_EVENT_CONNECT:
            log("CONNECT")
        elif ev == UVC_EVENT_DISCONNECT:
            log("DISCONNECT")
            self.stop_stream()
        else:
            log("event 0x%x" % ev)

    def _setup(self, data: bytes) -> None:
        bm, req = data[0], data[1]
        wvalue = data[2] | (data[3] << 8)
        windex = data[4] | (data[5] << 8)
        wlen = data[6] | (data[7] << 8)
        is_in = (bm & 0x80) != 0
        iface = windex & 0xFF
        entity = (windex >> 8) & 0xFF
        cs = (wvalue >> 8) & 0xFF
        log("SETUP bm=0x%x req=0x%x iface=%d ent=%d cs=0x%x len=%d" % (bm, req, iface, entity, cs, wlen))
        if iface == 1 and entity == 0 and cs in (UVC_VS_PROBE, UVC_VS_COMMIT):
            if is_in and req in (UVC_GET_CUR, UVC_GET_MIN, UVC_GET_MAX, UVC_GET_DEF):
                self.send_response(self.probe if cs == UVC_VS_PROBE else self.commit)
                return
            if is_in and req == UVC_GET_LEN:
                self.send_response(struct.pack("<H", 34))
                return
            if is_in and req == UVC_GET_INFO:
                self.send_response(b"\x03")
                return
            if (not is_in) and req == UVC_SET_CUR:
                self.pending_out = wlen
                self.send_response(None, wlen)
                return
        if iface == 0 and entity == 0 and cs == 0x02 and is_in and req == UVC_GET_CUR:
            self.send_response(bytes([self.err]))
            self.err = UVC_RC_NO_ERROR
            return
        if is_in and req == UVC_GET_INFO:
            self.send_response(b"\x03")
            return
        if is_in and req == UVC_GET_LEN:
            self.send_response(struct.pack("<H", min(wlen, 16) or 2))
            return
        if is_in:
            self.send_response(b"\x00" * min(wlen, 60))
            return
        if req == UVC_SET_CUR:
            self.pending_out = wlen
            self.send_response(None, wlen)
            return
        log("ack setup req=0x%x iface=%d ent=%d cs=0x%x" % (req, iface, entity, cs))
        self.send_response(b"" if is_in else None, 0 if is_in else wlen)

    def _data(self, data: bytes) -> None:
        length = struct.unpack_from("<i", data, 0)[0]
        payload = data[4 : 4 + max(length, 0)]
        if self.pending_out and length >= 10:
            # Keep our format/frame; accept interval if 15 or 10 fps.
            interval = 333333
            if len(payload) >= 8:
                got = struct.unpack_from("<I", payload, 4)[0]
                if got in (333333, 666666, 1000000, 2000000):
                    interval = got
            self.probe = pack_probe(interval)
            self.commit = self.probe
            self.pending_out = 0
            log("PROBE/COMMIT interval=%d fmt=%d frame=%d" % (
                interval,
                payload[2] if len(payload) > 2 else 0,
                payload[3] if len(payload) > 3 else 0,
            ))
            return
        self.pending_out = 0

    def _fill(self, idx: int, jpg: bytes) -> None:
        mm, length = self.maps[idx]
        n = min(len(jpg), length)
        mm.seek(0)
        mm.write(jpg[:n])
        buf = v4l2_buffer()
        buf.type = V4L2_BUF_TYPE_VIDEO_OUTPUT
        buf.memory = V4L2_MEMORY_MMAP
        buf.index = idx
        buf.bytesused = n
        buf.length = length
        buf.field = 1
        fcntl.ioctl(self.fd, VIDIOC_QBUF, buf)
        self.queued += 1

    def ensure_stream(self) -> bool:
        if self.streaming:
            return True
        jpg = read_live_jpeg()
        if not jpg:
            return False
        if not self.prepared:
            for i in range(self.nbuf):
                self._fill(i, jpg)
            self.prepared = True
        typ = ctypes.c_int(V4L2_BUF_TYPE_VIDEO_OUTPUT)
        try:
            fcntl.ioctl(self.fd, VIDIOC_STREAMON, typ)
        except OSError as exc:
            if exc.errno in (19, 16):
                return False
            raise
        self.streaming = True
        log("STREAMON queued=%d jpeg=%d" % (self.queued, len(jpg)))
        return True

    def stop_stream(self) -> None:
        if not self.streaming:
            return
        typ = ctypes.c_int(V4L2_BUF_TYPE_VIDEO_OUTPUT)
        try:
            fcntl.ioctl(self.fd, VIDIOC_STREAMOFF, typ)
        except OSError as exc:
            log("STREAMOFF %s" % exc)
        self.streaming = False
        self.queued = 0
        self.prepared = False
        log("STREAMOFF")

    def recycle(self) -> None:
        if not self.streaming:
            return
        jpg = read_live_jpeg()
        if not jpg:
            return
        r, _, _ = select.select([self.fd], [], [], 0)
        if not r:
            return
        buf = v4l2_buffer()
        buf.type = V4L2_BUF_TYPE_VIDEO_OUTPUT
        buf.memory = V4L2_MEMORY_MMAP
        try:
            fcntl.ioctl(self.fd, VIDIOC_DQBUF, buf)
        except OSError as exc:
            if exc.errno in (11, 16):
                return
            raise
        self.queued -= 1
        self._fill(buf.index, jpg)


def main() -> None:
    open(LOG, "w").write("bridge %dx%d\n" % (W, H))
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    uvc = None
    last_try = 0.0
    n = 0
    while True:
        try:
            if uvc is None:
                uvc = UvcOut(find_uvc())
                uvc.setup()
            r, _, x = select.select([uvc.fd], [], [uvc.fd], 0.05)
            if x and uvc.events:
                try:
                    uvc.handle_event()
                except OSError as exc:
                    if exc.errno not in (11, 2):
                        log("event %s" % exc)
            if uvc.streaming:
                try:
                    uvc.recycle()
                except OSError as exc:
                    if exc.errno == 22:
                        uvc.stop_stream()
                    else:
                        raise
                n += 1
                if n == 1 or n % 120 == 0:
                    log("running queued=%d" % uvc.queued)
            elif time.monotonic() - last_try > 0.3:
                last_try = time.monotonic()
                try:
                    uvc.ensure_stream()
                except OSError as exc:
                    if exc.errno != 22:
                        raise
                    log("stream wait %s" % exc)
        except OSError as exc:
            log("uvc %s" % exc)
            try:
                if uvc:
                    os.close(uvc.fd)
            except Exception:
                pass
            uvc = None
            time.sleep(0.4)
        except Exception as exc:
            log("err %s" % exc)
            time.sleep(0.2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
