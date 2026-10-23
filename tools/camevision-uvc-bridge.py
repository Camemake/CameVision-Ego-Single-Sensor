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
    SIZES = ((1400, 1600), (1050, 1200), (700, 800), (350, 400))
else:
    SIZES = ((1920, 1200), (1280, 800), (960, 600), (640, 400))
TWELVE = os.path.isfile("/tmp/camevision-uvc-12frames") or AM
if TWELVE:
    FRAMES = tuple(SIZES[i // 3] for i in range(12))
else:
    FRAMES = SIZES
W, H = SIZES[0]
MAX_FRAME = W * H * 2
LIVE_JPG = "/tmp/camevision-live.jpg"
UVC_JPG = "/tmp/camevision-uvc.jpg"
CTL_PATH = "/tmp/camevision-uvc-ctl.json"
LOG = "/userdata/cv-uvc-bridge.log"
INTERVALS = (166666, 333333, 666666)
CT_ID = 1
PU_IDS = (2, 6)
# Camera terminal
CT_AE_MODE = 0x02
CT_AE_PRIORITY = 0x03
CT_EXPOSURE_ABS = 0x04
# Processing unit
PU_BACKLIGHT = 0x01
PU_BRIGHTNESS = 0x02
PU_CONTRAST = 0x03
PU_GAIN = 0x04
PU_POWERLINE = 0x05
PU_SATURATION = 0x07
PU_SHARPNESS = 0x08
PU_GAMMA = 0x09
PU_WB_TEMP = 0x0A
PU_WB_AUTO = 0x0B

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
        if any(s in low for s in ("gadget", "uvc", "camevision", "camemake", "came", "dummy_udc", "f_uvc")):
            hits.append(("/dev/" + ent, name))
    if hits:
        log("uvc node %s (%s)" % (hits[0][0], hits[0][1]))
        return hits[0][0]
    raise OSError("no UVC gadget video node")


def read_live_jpeg() -> bytes:
    for path in (UVC_JPG, LIVE_JPG):
        try:
            data = open(path, "rb").read()
        except OSError:
            continue
        if len(data) >= 200 and data[:2] == b"\xff\xd8":
            return data
    return b""


FMT_INDEX = 1


def snap_interval(got: int) -> int:
    if got in INTERVALS:
        return got
    best = INTERVALS[0]
    err = abs(got - best) if got else best
    for cand in INTERVALS:
        d = abs(got - cand)
        if d < err:
            best, err = cand, d
    return best


def frame_of(index: int) -> tuple[int, int, int]:
    if 1 <= index <= len(FRAMES):
        w, h = FRAMES[index - 1]
        return index, w, h
    w, h = FRAMES[0]
    return 1, w, h


def pack_probe(frame: int = 1, interval: int = 166666) -> bytes:
    idx, w, h = frame_of(frame)
    return struct.pack(
        "<HBBIHHHHHIII BBBB",
        0,
        FMT_INDEX,
        idx,
        snap_interval(interval),
        0,
        0,
        0,
        0,
        0,
        w * h * 2,
        1024,
        48000000,
        0,
        1,
        1,
        1,
    )


def s16(n: int) -> bytes:
    return struct.pack("<h", max(-32768, min(32767, int(n))))


def u16(n: int) -> bytes:
    return struct.pack("<H", max(0, min(65535, int(n))))


def u32(n: int) -> bytes:
    return struct.pack("<I", max(0, int(n)) & 0xFFFFFFFF)


class Controls:
    """Standard UVC CT/PU values Windows Camera maps to sliders."""

    def __init__(self) -> None:
        self.ae = 1  # manual so shutter/exposure sliders work
        self.ae_priority = 0
        self.exposure = 300  # 30.0 ms, 100 µs units
        self.brightness = 8
        self.contrast = 36
        self.saturation = 32
        self.sharpness = 16
        self.gamma = 90
        self.gain = 44
        self.backlight = 0
        self.powerline = 1
        self.wb_temp = 4500
        self.wb_auto = 1
        self.frame = 1
        self.interval = 333333
        self._write()

    def fps(self) -> int:
        return {166666: 60, 333333: 30, 666666: 15}.get(self.interval, 60)

    def size(self) -> tuple[int, int]:
        return frame_of(self.frame)[1:]

    def dump(self) -> dict:
        w, h = self.size()
        return {
            "w": w,
            "h": h,
            "fps": self.fps(),
            "ae": self.ae,
            "exposure": self.exposure,
            "ae_priority": self.ae_priority,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "sharpness": self.sharpness,
            "gamma": self.gamma,
            "gain": self.gain,
            "backlight": self.backlight,
            "powerline": self.powerline,
            "wb_temp": self.wb_temp,
            "wb_auto": self.wb_auto,
        }

    def _write(self) -> None:
        raw = (
            "{\n"
            + ",\n".join('  "%s": %s' % (k, v) for k, v in self.dump().items())
            + "\n}\n"
        )
        tmp = CTL_PATH + ".tmp"
        try:
            with open(tmp, "w") as fh:
                fh.write(raw)
            os.replace(tmp, CTL_PATH)
        except OSError as exc:
            log("ctl %s" % exc)

    def get(self, entity: int, cs: int, req: int, wlen: int) -> bytes | None:
        spec = self._spec(entity, cs)
        if spec is None:
            return None
        cur, mn, mx, res, default, info = spec
        if req == UVC_GET_INFO:
            return bytes([info])
        if req == UVC_GET_LEN:
            return struct.pack("<H", len(cur))
        if req == UVC_GET_MIN:
            return mn
        if req == UVC_GET_MAX:
            return mx
        if req == UVC_GET_RES:
            return res
        if req == UVC_GET_DEF:
            return default
        if req in (UVC_GET_CUR,):
            return cur
        return cur[: min(len(cur), wlen)]

    def set(self, entity: int, cs: int, payload: bytes) -> bool:
        if entity == CT_ID:
            if cs == CT_AE_MODE and payload:
                self.ae = 2 if payload[0] & 2 else 1
            elif cs == CT_AE_PRIORITY and payload:
                self.ae_priority = 1 if payload[0] else 0
            elif cs == CT_EXPOSURE_ABS and len(payload) >= 4:
                self.exposure = max(1, min(666, struct.unpack_from("<I", payload)[0]))
            else:
                return False
        elif entity in PU_IDS:
            if cs == PU_BRIGHTNESS and len(payload) >= 2:
                self.brightness = max(-64, min(64, struct.unpack_from("<h", payload)[0]))
            elif cs == PU_CONTRAST and len(payload) >= 2:
                self.contrast = max(0, min(64, struct.unpack_from("<h", payload)[0]))
            elif cs == PU_SATURATION and len(payload) >= 2:
                self.saturation = max(0, min(64, struct.unpack_from("<h", payload)[0]))
            elif cs == PU_SHARPNESS and len(payload) >= 2:
                self.sharpness = max(0, min(64, struct.unpack_from("<h", payload)[0]))
            elif cs == PU_GAMMA and len(payload) >= 2:
                self.gamma = max(80, min(160, struct.unpack_from("<h", payload)[0]))
            elif cs == PU_GAIN and len(payload) >= 2:
                self.gain = max(0, min(128, struct.unpack_from("<h", payload)[0]))
            elif cs == PU_BACKLIGHT and len(payload) >= 2:
                self.backlight = 1 if struct.unpack_from("<h", payload)[0] else 0
            elif cs == PU_POWERLINE and payload:
                self.powerline = payload[0] if payload[0] in (0, 1, 2) else 1
            elif cs == PU_WB_TEMP and len(payload) >= 2:
                self.wb_temp = max(2800, min(6500, struct.unpack_from("<h", payload)[0]))
            elif cs == PU_WB_AUTO and payload:
                self.wb_auto = 1 if payload[0] else 0
            else:
                return False
        else:
            return False
        self._write()
        return True

    def _spec(self, entity: int, cs: int):
        # cur, min, max, res, def, info(GET+SET)
        info = 0x03
        if entity == CT_ID:
            if cs == CT_AE_MODE:
                return bytes([self.ae]), b"\x01", b"\x02", b"\x03", b"\x01", info
            if cs == CT_AE_PRIORITY:
                return bytes([self.ae_priority]), b"\x00", b"\x01", b"\x01", b"\x00", info
            if cs == CT_EXPOSURE_ABS:
                return (
                    u32(self.exposure),
                    u32(1),
                    u32(666),
                    u32(1),
                    u32(180),
                    info,
                )
        if entity in PU_IDS:
            if cs == PU_BRIGHTNESS:
                return s16(self.brightness), s16(-64), s16(64), s16(1), s16(8), info
            if cs == PU_CONTRAST:
                return s16(self.contrast), s16(0), s16(64), s16(1), s16(32), info
            if cs == PU_SATURATION:
                return s16(self.saturation), s16(0), s16(64), s16(1), s16(32), info
            if cs == PU_SHARPNESS:
                return s16(self.sharpness), s16(0), s16(64), s16(1), s16(16), info
            if cs == PU_GAMMA:
                return s16(self.gamma), s16(80), s16(160), s16(1), s16(100), info
            if cs == PU_GAIN:
                return s16(self.gain), s16(0), s16(128), s16(1), s16(32), info
            if cs == PU_BACKLIGHT:
                return s16(self.backlight), s16(0), s16(1), s16(1), s16(0), info
            if cs == PU_POWERLINE:
                return bytes([self.powerline]), b"\x00", b"\x02", b"\x01", b"\x01", info
            if cs == PU_WB_TEMP:
                return s16(self.wb_temp), s16(2800), s16(6500), s16(100), s16(4500), info
            if cs == PU_WB_AUTO:
                return bytes([self.wb_auto]), b"\x00", b"\x01", b"\x01", b"\x01", info
        return None


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
        self.pending_cs = 0
        self.pending_ent = 0
        self.prepared = False
        self.ctl = Controls()
        self.probe = pack_probe(self.ctl.frame, self.ctl.interval)
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
                self.pending_cs = cs
                self.pending_ent = 0
                self.send_response(None, wlen)
                return
        if iface == 0 and (entity == CT_ID or entity in PU_IDS):
            if is_in:
                data = self.ctl.get(entity, cs, req, wlen)
                if data is not None:
                    self.send_response(data[: min(len(data), 60)])
                    return
            elif req == UVC_SET_CUR:
                self.pending_out = wlen
                self.pending_cs = cs
                self.pending_ent = entity
                self.send_response(None, wlen)
                return
        if iface == 0 and entity == 0 and cs == 0x02 and is_in and req == UVC_GET_CUR:
            self.send_response(bytes([self.err]))
            self.err = UVC_RC_NO_ERROR
            return
        if is_in and req == UVC_GET_INFO:
            self.send_response(b"\x00")
            return
        if is_in and req == UVC_GET_LEN:
            self.send_response(struct.pack("<H", min(wlen, 16) or 2))
            return
        if is_in:
            self.send_response(b"\x00" * min(wlen, 60))
            return
        if req == UVC_SET_CUR:
            self.pending_out = wlen
            self.pending_cs = cs
            self.pending_ent = entity
            self.send_response(None, wlen)
            return
        log("ack setup req=0x%x iface=%d ent=%d cs=0x%x" % (req, iface, entity, cs))
        self.send_response(b"" if is_in else None, 0 if is_in else wlen)

    def _data(self, data: bytes) -> None:
        length = struct.unpack_from("<i", data, 0)[0]
        payload = data[4 : 4 + max(length, 0)]
        if (self.pending_ent == CT_ID or self.pending_ent in PU_IDS) and self.pending_out:
            ok = self.ctl.set(self.pending_ent, self.pending_cs, payload)
            log(
                "SET ent=%d cs=0x%x ok=%s bytes=%s"
                % (self.pending_ent, self.pending_cs, ok, payload[:8].hex())
            )
            self.pending_out = 0
            self.pending_ent = 0
            self.pending_cs = 0
            return
        if self.pending_out and length >= 8:
            want_frame = payload[3] if len(payload) > 3 else 1
            got = struct.unpack_from("<I", payload, 4)[0] if len(payload) >= 8 else 166666
            frame, w, h = frame_of(want_frame)
            interval = snap_interval(got)
            self.ctl.frame = frame
            self.ctl.interval = interval
            self.ctl._write()
            self.probe = pack_probe(frame, interval)
            self.commit = self.probe
            self.pending_out = 0
            log(
                "PROBE/COMMIT mjpeg %dx%d frame=%d interval=%d fps=%d"
                % (w, h, frame, interval, self.ctl.fps())
            )
            return
        self.pending_out = 0
        self.pending_ent = 0
        self.pending_cs = 0

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
        while True:
            buf = v4l2_buffer()
            buf.type = V4L2_BUF_TYPE_VIDEO_OUTPUT
            buf.memory = V4L2_MEMORY_MMAP
            try:
                fcntl.ioctl(self.fd, VIDIOC_DQBUF, buf)
            except OSError as exc:
                if exc.errno in (11, 16, 61):
                    return
                raise
            self.queued -= 1
            self._fill(buf.index, jpg)


def main() -> None:
    open(LOG, "w").write("bridge %dx%d\n" % (W, H))
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    uvc = None
    n = 0
    while True:
        try:
            if uvc is None:
                uvc = UvcOut(find_uvc())
                uvc.setup()
            r, _, x = select.select([uvc.fd], [], [uvc.fd], 0.002)
            # V4L2 events are POLLPRI (x) and sometimes POLLIN (r).
            if uvc.events and (r or x):
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
