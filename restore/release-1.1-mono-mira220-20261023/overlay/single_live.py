#!/usr/bin/env python3
"""CameVision Single live page: one camera + one IMU over ADB HTTP.

SC233HGS uses ISP NV12 on /dev/video13. MIRA220 AM uses CIF RAW10 on
/dev/video1 (same path as Ego AM CAM0, minus the second eye).
"""
from __future__ import annotations

import ctypes
import fcntl
import mmap
import os
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.request
from ctypes import (
    CDLL,
    POINTER,
    byref,
    c_int,
    c_ubyte,
    c_ulong,
    c_void_p,
    cast,
    string_at,
)

AM = os.path.isfile("/userdata/camevision-am.on")
if AM:
    CAM_W, CAM_H = 1600, 1400
    # Ego AM: capture 1600×1400 GRBG, then 90° CCW → 1400×1600 on the page.
    VIEW_W, VIEW_H = CAM_H, CAM_W
    DEV = "/dev/video1"
    RAW_STRIDE = 2048
    RAW_FRAME = RAW_STRIDE * CAM_H
    LIVE_EXPOSURE = 3600
    LIVE_VBLANK = 2695
    I2C_SLAVE_FORCE = 0x0706
    COLOR_SO = "/userdata/libsingle_color.so"
else:
    CAM_W, CAM_H = 1920, 1200
    VIEW_W, VIEW_H = CAM_W, CAM_H
    DEV = "/dev/video13"
    RAW_STRIDE = 0
    RAW_FRAME = 0
    COLOR_SO = ""
CAM_FRAME = CAM_W * CAM_H * 3 // 2
VIEW_FRAME = VIEW_W * VIEW_H * 3 // 2
PORT = 8081
IMU_URL = "http://127.0.0.1:8083/"
TJ = "/oem/usr/lib/libturbojpeg.so"
LOGO = "/userdata/camemake-logo.png"
LIVE_JPG = "/tmp/camevision-live.jpg"
RECORD_FLAG = "/tmp/camevision-record.on"
RECORD_FIFO = "/tmp/camevision-nv12.fifo"
RECORD_GEOM = "/tmp/camevision-record.geom"
AIM_FLAG = "/tmp/camevision-aim.on"
AIM_JPG = "/tmp/camevision-aim.jpg"
UVC_CTL = "/tmp/camevision-uvc-ctl.json"
UVC_JPG = "/tmp/camevision-uvc.jpg"
CAP_FPS = 60
NATIVE = None


def _load_native() -> None:
    global NATIVE
    if not AM:
        return
    for path in (COLOR_SO,):
        if not path or not os.path.exists(path):
            continue
        try:
            lib = CDLL(path)
            lib.ego_raw10_color_nv12.argtypes = [
                POINTER(c_ubyte),
                c_int,
                c_int,
                c_int,
                POINTER(c_ubyte),
                POINTER(c_ubyte),
                POINTER(c_ubyte),
                POINTER(c_ubyte),
            ]
            lib.ego_raw10_color_nv12.restype = None
            NATIVE = lib
            print("mira220: native color %s" % path, flush=True)
            return
        except Exception as exc:
            print("mira220 native", path, type(exc).__name__, exc, flush=True)
    print("mira220: numpy color fallback (no native decoder)", flush=True)


_load_native()

shared: dict = {"cam0": None, "cam0_fps": 0.0, "jpg": b"", "jpg_t": 0.0}


BRAND_NAME = "CameVision Ego Single Sensor"
BRAND_SUB = "MIRA220 RGB · 1 IMU" if AM else "Camemake · 1 sensor · 1 IMU"

PAGE = (
    b"""<!doctype html>
<html><head><meta charset="utf-8"><title>Camemake | """
    + BRAND_NAME.encode()
    + b"""</title>
<link rel="icon" href="/brand.png">
<style>
 :root{--came:#1a6f7c;--pink:#e84b8a;--bg:#f4efe8;--ink:#222;--muted:#5c5c5c;--line:#e4ddd4}
 html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);
  font-family:Segoe UI,Helvetica Neue,Arial,sans-serif;overflow:hidden}
 .brand{height:72px;display:flex;align-items:center;gap:16px;padding:0 22px;
  background:#fff;border-bottom:1px solid var(--line)}
 .plate img{height:28px;width:auto;display:block}
 .titles{display:flex;flex-direction:column;line-height:1.2}
 .titles b{font-size:20px;font-weight:800;color:#1a1a1a}
 .titles span{font-size:13px;color:var(--came)}
 .stage{height:calc(100% - 72px);padding:12px;box-sizing:border-box}
 .pane{height:100%;position:relative;background:#111;border-radius:10px;overflow:hidden}
 .pane img.v{width:100%;height:100%;object-fit:contain;object-position:center;display:block;background:#111}
 .hud{position:absolute;left:10px;top:10px;background:rgba(255,255,255,.88);color:#222;
  padding:8px 10px;border-radius:8px;font:12px Consolas,monospace;white-space:pre;
  box-shadow:0 1px 4px rgba(0,0,0,.12)}
</style></head><body>
<div class="brand">
 <div class="plate"><img src="/brand.png" alt="Camemake"></div>
 <div class="titles"><b>"""
    + BRAND_NAME.encode()
    + b"""</b><span>"""
    + BRAND_SUB.encode()
    + b"""</span></div>
</div>
<div class="stage">
 <div class="pane"><img class="v" id="v" src="/ov0"><div class="hud" id="h">CAM0 IMU0</div></div>
</div>
<script>
function n(v,d){return (v===undefined||Number.isNaN(+v))?"-":Number(v).toFixed(d)}
async function tick(){
 let s={}, imu={};
 try{ s=await (await fetch("/stat")).json(); }catch(e){}
 try{ imu=await (await fetch("/imu")).json(); }catch(e){}
 const i=imu.imu0||{};
 document.getElementById("h").textContent =
  "CAM0  "+((s&&s.dev)||"/dev/video13")+"\\n"+
  (i.t_iso||s.t||"")+"\\n"+
  "CAM "+n(s.cam0_fps,0)+" fps   IMU "+n(i.read_hz||imu.read_hz,0)+" Hz\\n"+
  "|a| "+n(i.a_g,3)+" g   w "+n(i.gx,1)+" "+n(i.gy,1)+" "+n(i.gz,1)+"\\n"+
  ((s&&s.w)||"""
    + str(VIEW_W).encode()
    + b""")+"x"+((s&&s.h)||"""
    + str(VIEW_H).encode()
    + b""")+" "+((s&&s.fmt)||"NV12");
}
setInterval(tick, 250);
tick();
</script></body></html>
"""
)


class TurboEnc:
    def __init__(self, w: int, h: int, q: int = 70) -> None:
        self.w, self.h, self.q = w, h, q
        lib = CDLL(TJ)
        lib.tjInitCompress.restype = c_void_p
        lib.tjCompressFromYUVPlanes.restype = c_int
        lib.tjCompressFromYUVPlanes.argtypes = [
            c_void_p,
            POINTER(POINTER(c_ubyte)),
            c_int,
            POINTER(c_int),
            c_int,
            c_int,
            POINTER(c_void_p),
            POINTER(c_ulong),
            c_int,
            c_int,
        ]
        lib.tjDestroy.argtypes = [c_void_p]
        lib.tjFree.argtypes = [c_void_p]
        self.lib = lib
        self.hnd = lib.tjInitCompress()
        if not self.hnd:
            raise OSError("tjInitCompress")
        self.lk = threading.Lock()
        uvn = (w * h) // 4
        self._u = bytearray(uvn)
        self._v = bytearray(uvn)
        self._u_c = (c_ubyte * uvn).from_buffer(self._u)
        self._v_c = (c_ubyte * uvn).from_buffer(self._v)

    def encode(self, nv12) -> bytes:
        w, h = self.w, self.h
        ysz = w * h
        src = nv12 if isinstance(nv12, bytearray) else bytearray(nv12)
        y = (c_ubyte * ysz).from_buffer(src)
        uv_len = ysz // 2
        uv = src[ysz : ysz + uv_len]
        self._u[:] = uv[0::2]
        self._v[:] = uv[1::2]
        planes = (POINTER(c_ubyte) * 3)(
            cast(y, POINTER(c_ubyte)),
            cast(self._u_c, POINTER(c_ubyte)),
            cast(self._v_c, POINTER(c_ubyte)),
        )
        strides = (c_int * 3)(w, w // 2, w // 2)
        jpeg_buf = c_void_p()
        jpeg_size = c_ulong(0)
        with self.lk:
            rc = self.lib.tjCompressFromYUVPlanes(
                self.hnd,
                planes,
                w,
                strides,
                h,
                2,
                byref(jpeg_buf),
                byref(jpeg_size),
                self.q,
                2048,
            )
        if rc != 0 or not jpeg_buf.value:
            return b""
        try:
            return string_at(jpeg_buf, jpeg_size.value)
        finally:
            self.lib.tjFree(jpeg_buf)


_I2C_LOCK = threading.Lock()


def _i2c_wr16(bus: int, reg: int, val: int) -> None:
    with _I2C_LOCK:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
        try:
            fcntl.ioctl(fd, I2C_SLAVE_FORCE, 0x54)
            os.write(fd, bytes([reg >> 8, reg & 0xFF, val & 0xFF, val >> 8]))
        finally:
            os.close(fd)


def _i2c_rd16(bus: int, reg: int) -> int:
    with _I2C_LOCK:
        fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
        try:
            fcntl.ioctl(fd, I2C_SLAVE_FORCE, 0x54)
            os.write(fd, bytes([reg >> 8, reg & 0xFF]))
            b = os.read(fd, 2)
            return b[0] | (b[1] << 8)
        finally:
            os.close(fd)


def load_uvc_ctl() -> dict:
    try:
        import json

        with open(UVC_CTL, "r") as fh:
            got = json.load(fh)
        if isinstance(got, dict):
            shared["_uvc_ctl"] = got
            return got
    except Exception:
        pass
    return shared.get("_uvc_ctl") or {}


def set_live_30fps() -> None:
    """Keep Ego AM window + the UVC / live exposure on the sensor.

    The mira220 driver rewrites VSTART=64 and EXP=1000 on stream-on.
    VSTART≠0 slides 64 dummy rows into the frame; after 90° CCW that is
    a bad right edge. Re-apply like Ego (after STREAMON and every few s).
    """
    if not AM:
        return
    ctl = load_uvc_ctl()
    fps = int(ctl.get("fps") or 30)
    if fps not in (15, 30, 60):
        fps = 30
    line_us = 8.14
    frame_lines = int(round(1000000.0 / (fps * line_us)))
    vblank = max(16, frame_lines - CAM_H)
    pl = int(ctl.get("powerline") or 0)
    period_us = 10000 if pl == 1 else 8333 if pl == 2 else 0
    if int(ctl.get("ae") or 1) == 2:
        exp = 3600 if fps <= 30 else 1800
        if int(ctl.get("backlight") or 0):
            exp = int(exp * 1.25)
        if period_us:
            exp_us_a = max(period_us, int((int(exp * line_us) + period_us / 2) / period_us) * period_us)
            exp = exp_us_a / line_us
        exp = min(frame_lines - 8, int(exp))
    else:
        exp_us = max(100, int(ctl.get("exposure") or 300) * 100)
        if period_us:
            exp_us = max(period_us, int((exp_us + period_us / 2) / period_us) * period_us)
        exp = max(8, min(frame_lines - 8, int(exp_us / line_us)))
    try:
        _i2c_wr16(3, 0x107D, 0)
        _i2c_wr16(3, 0x200A, 0)
        _i2c_wr16(3, 0x1087, CAM_H)
        _i2c_wr16(3, 0x2008, CAM_W // 2)
        _i2c_wr16(3, 0x207D, CAM_W)
        _i2c_wr16(3, 0x100C, exp)
        _i2c_wr16(3, 0x1012, vblank)
        _i2c_wr16(3, 0x1103, vblank)
        vstart = _i2c_rd16(3, 0x107D)
        got_exp = _i2c_rd16(3, 0x100C)
        got_vb = _i2c_rd16(3, 0x1012)
        sig = (got_exp, got_vb, vstart, fps)
        if shared.get("_mira_sig") != sig:
            print(
                "mira220: exp %d vblank %d vstart %d fps %d"
                % (got_exp, got_vb, vstart, fps),
                flush=True,
            )
            shared["_mira_sig"] = sig
    except Exception as exc:
        print("mira220 fps", exc, flush=True)


_RAW_SCR = {}
_LUT_R_C = _LUT_G_C = _LUT_B_C = None


def _awb_lut_c():
    """Official Ego AM ISP: R×1.90 G×1.38 B×3.06, black-10.

    UVC sliders only lift and gain after that AWB. Rebuilding the color
    matrix from contrast/gamma/saturation made a green picture.
    """
    global _LUT_R_C, _LUT_G_C, _LUT_B_C
    ctl = shared.get("_uvc_ctl") or {}
    gain = (int(ctl.get("gain") or 32) + 32) / 64.0
    bright = int(ctl.get("brightness") or 0)
    sig = (gain, bright)
    if _LUT_R_C is not None and shared.get("_lut_sig") == sig:
        return _LUT_R_C, _LUT_G_C, _LUT_B_C
    r = bytearray(1024)
    g = bytearray(1024)
    b = bytearray(1024)
    for x in range(1024):
        u8 = (x >> 2) - 10 + bright
        if u8 < 0:
            u8 = 0
        elif u8 > 255:
            u8 = 255
        rr = int(u8 * 1.90 * gain)
        gg = int(u8 * 1.38 * gain)
        bb = int(u8 * 3.06 * gain)
        r[x] = 255 if rr > 255 else rr
        g[x] = 255 if gg > 255 else gg
        b[x] = 255 if bb > 255 else bb
    _LUT_R_C = (c_ubyte * 1024).from_buffer(r)
    _LUT_G_C = (c_ubyte * 1024).from_buffer(g)
    _LUT_B_C = (c_ubyte * 1024).from_buffer(b)
    shared["_awb_keep"] = (r, g, b)
    shared["_lut_sig"] = sig
    return _LUT_R_C, _LUT_G_C, _LUT_B_C


def _raw_scratch():
    import numpy as np

    s = _RAW_SCR
    if s.get("bayer") is None:
        s["bayer"] = np.empty((CAM_H, CAM_W), dtype=np.uint8)
        s["bgr"] = np.empty((VIEW_H, VIEW_W, 3), dtype=np.uint8)
        x = np.arange(1024, dtype=np.int16)
        u8 = np.clip((x >> 2) - 10, 0, 255).astype(np.int16)
        s["lut_b"] = np.clip(u8 * 3.06, 0, 255).astype(np.uint8)
        s["lut_g"] = np.clip(u8 * 1.38, 0, 255).astype(np.uint8)
        s["lut_r"] = np.clip(u8 * 1.90, 0, 255).astype(np.uint8)
    return s


def raw10_to_nv12(raw, dst):
    """CIF compact RAW10 (LE 40-bit) GRBG → 1400×1600 NV12 (90° CCW).

    Same unpack, AWB LUTs, and rotate as Ego AM ``ego_raw10_color_nv12``.
    """
    packed = memoryview(raw)[:RAW_FRAME]
    if dst is None or len(dst) < VIEW_FRAME:
        dst = bytearray(VIEW_FRAME)
    if NATIVE is not None:
        try:
            lr, lg, lb = _awb_lut_c()
            src_p = (c_ubyte * RAW_FRAME).from_buffer(packed)
            dst_p = (c_ubyte * VIEW_FRAME).from_buffer(dst)
            NATIVE.ego_raw10_color_nv12(
                src_p, RAW_STRIDE, CAM_W, CAM_H, dst_p, lr, lg, lb
            )
            return dst
        except Exception as exc:
            if not shared.get("_raw_native_err"):
                print("raw10 native", type(exc).__name__, exc, flush=True)
                shared["_raw_native_err"] = True
    try:
        import cv2
        import numpy as np

        scr = _raw_scratch()
        rows = np.frombuffer(packed, dtype=np.uint8, count=RAW_STRIDE * CAM_H).reshape(
            CAM_H, RAW_STRIDE
        )
        grp = rows[:, : (CAM_W * 10) // 8].reshape(CAM_H, CAM_W // 4, 5)
        b0, b1, b2, b3, b4 = [grp[:, :, i].astype(np.uint16) for i in range(5)]
        p0 = b0 | ((b1 & 3) << 8)
        p1 = (b1 >> 2) | ((b2 & 15) << 6)
        p2 = (b2 >> 4) | ((b3 & 63) << 4)
        p3 = (b3 >> 6) | (b4 << 2)
        bayer = scr["bayer"]
        bayer[:, 0::4] = scr["lut_g"][p0]
        bayer[:, 1::4] = scr["lut_r"][p1]
        bayer[:, 2::4] = scr["lut_g"][p2]
        bayer[:, 3::4] = scr["lut_r"][p3]
        # Odd rows are B G B G — overwrite from the same packed groups.
        bayer[1::2, 0::4] = scr["lut_b"][p0[1::2]]
        bayer[1::2, 1::4] = scr["lut_g"][p1[1::2]]
        bayer[1::2, 2::4] = scr["lut_b"][p2[1::2]]
        bayer[1::2, 3::4] = scr["lut_g"][p3[1::2]]
        bgr = cv2.cvtColor(bayer, cv2.COLOR_BAYER_GR2BGR)
        cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE, dst=scr["bgr"])
        yuv = cv2.cvtColor(scr["bgr"], cv2.COLOR_BGR2YUV)
        out = np.frombuffer(dst, dtype=np.uint8)
        out[: VIEW_W * VIEW_H] = yuv[:, :, 0].reshape(-1)
        uv = out[VIEW_W * VIEW_H :].reshape(VIEW_H // 2, VIEW_W)
        uv[:, 0::2] = yuv[0::2, 0::2, 1]
        uv[:, 1::2] = yuv[0::2, 0::2, 2]
        return dst
    except Exception as exc:
        if not shared.get("_raw_err"):
            print("raw10", type(exc).__name__, exc, flush=True)
            shared["_raw_err"] = True
    y = memoryview(dst)[: VIEW_W * VIEW_H]
    uv = memoryview(dst)[VIEW_W * VIEW_H :]
    for i in range(len(uv)):
        uv[i] = 128
    y[:] = bytes(len(y))
    return dst


class CifMmap:
    """rkcif multiplanar BG10. Same ioctl layout as Ego AM."""

    TYPE = 9
    MEM = 1
    FMT_SIZE = 208
    REQ_SIZE = 20
    BUF_SIZE = 88
    PLANE_SIZE = 64
    NBUF = 4

    def __init__(self, dev: str) -> None:
        self.fd = os.open(dev, os.O_RDWR)
        self.maps = []
        self._held = None
        self._planes = [bytearray(self.PLANE_SIZE) for _ in range(self.NBUF + 1)]
        fmt = bytearray(self.FMT_SIZE)
        struct.pack_into("<I", fmt, 0, self.TYPE)
        struct.pack_into("<III", fmt, 8, CAM_W, CAM_H, 0x30314742)
        fcntl.ioctl(self.fd, self._ioc(3, 5, self.FMT_SIZE), fmt)
        req = bytearray(self.REQ_SIZE)
        struct.pack_into("<III", req, 0, self.NBUF, self.TYPE, self.MEM)
        fcntl.ioctl(self.fd, self._ioc(3, 8, self.REQ_SIZE), req)
        nbuf = struct.unpack_from("<I", req, 0)[0]
        for i in range(nbuf):
            planes = self._planes[i]
            buf = self._buf(i, planes)
            fcntl.ioctl(self.fd, self._ioc(3, 9, self.BUF_SIZE), buf)
            length = struct.unpack_from("<I", planes, 4)[0]
            offset = struct.unpack_from("<I", planes, 8)[0]
            mm = mmap.mmap(
                self.fd,
                length,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=offset,
            )
            self.maps.append(mm)
            fcntl.ioctl(self.fd, self._ioc(3, 15, self.BUF_SIZE), buf)
        typ = bytearray(4)
        struct.pack_into("<I", typ, 0, self.TYPE)
        fcntl.ioctl(self.fd, self._ioc(1, 18, 4), typ)
        self._typ = typ

    @staticmethod
    def _ioc(dir_, nr, size):
        return (dir_ << 30) | (size << 16) | (ord("V") << 8) | nr

    def _ptr(self, ba):
        return ctypes.addressof((ctypes.c_char * len(ba)).from_buffer(ba))

    def _buf(self, index, planes):
        buf = bytearray(self.BUF_SIZE)
        struct.pack_into("<I", buf, 0, index)
        struct.pack_into("<I", buf, 4, self.TYPE)
        struct.pack_into("<I", buf, 60, self.MEM)
        struct.pack_into("<Q", buf, 64, self._ptr(planes))
        struct.pack_into("<I", buf, 72, 1)
        return buf

    def grab_raw(self):
        planes = self._planes[-1]
        buf = self._buf(0, planes)
        struct.pack_into("<I", buf, 0, 0)
        fcntl.ioctl(self.fd, self._ioc(3, 17, self.BUF_SIZE), buf)
        idx = struct.unpack_from("<I", buf, 0)[0]
        self._held = buf
        return self.maps[idx]

    def release(self) -> None:
        buf = getattr(self, "_held", None)
        if buf is None:
            return
        fcntl.ioctl(self.fd, self._ioc(3, 15, self.BUF_SIZE), buf)
        self._held = None

    def close(self) -> None:
        try:
            fcntl.ioctl(self.fd, self._ioc(1, 19, 4), self._typ)
        except Exception:
            pass
        for mm in self.maps:
            try:
                mm.close()
            except Exception:
                pass
        try:
            os.close(self.fd)
        except Exception:
            pass


def _mark_fps() -> None:
    now = time.monotonic()
    shared["cam0_t"] = now
    t0 = shared.get("cam0_fps_t")
    n = int(shared.get("cam0_n") or 0) + 1
    if t0 is None:
        shared["cam0_fps_t"] = now
        shared["cam0_n"] = 1
    elif now - float(t0) >= 1.0:
        shared["cam0_fps"] = n / (now - float(t0))
        shared["cam0_n"] = 0
        shared["cam0_fps_t"] = now
    else:
        shared["cam0_n"] = n


def grab_am() -> None:
    ring = [bytearray(VIEW_FRAME) for _ in range(3)]
    slot = 0
    set_live_30fps()
    while True:
        cap = None
        try:
            cap = CifMmap(DEV)
            set_live_30fps()
            print("grab cam0: cif mmap %s" % DEV, flush=True)
            while True:
                raw = cap.grab_raw()
                raw10_to_nv12(raw, dst=ring[slot])
                cap.release()
                shared["cam0"] = ring[slot]
                _mark_fps()
                slot = (slot + 1) % 3
        except Exception as exc:
            print("grab mmap", type(exc).__name__, exc, flush=True)
            time.sleep(0.2)
        finally:
            if cap is not None:
                cap.close()
        time.sleep(0.05)


def grab() -> None:
    if AM:
        grab_am()
        return

    live = "/tmp/cam0.nv12"
    try:
        os.remove(live)
    except OSError:
        pass
    os.mkfifo(live)
    ring = [bytearray(CAM_FRAME) for _ in range(4)]
    slot = 0
    while True:
        # Same FIFO handshake as Ego. Do not set flip or S_PARM here —
        # video13 rejects VIDIOC_S_PARM, and flip-on-restart wedges MIPI.
        cmd = (
            f"v4l2-ctl -d {DEV} --set-fmt-video=width={CAM_W},height={CAM_H},pixelformat=NV12 "
            f"--stream-mmap=8 --stream-to={live} --stream-poll"
        )
        proc = subprocess.Popen(["sh", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.15)
        try:
            if proc.poll() is not None:
                time.sleep(0.2)
                continue
            with open(live, "rb") as fh:
                while proc.poll() is None:
                    mv = memoryview(ring[slot])
                    got = 0
                    while got < CAM_FRAME:
                        n = fh.readinto(mv[got:])
                        if not n:
                            got = 0
                            break
                        got += n
                    if got != CAM_FRAME:
                        break
                    shared["cam0"] = ring[slot]
                    now = time.monotonic()
                    shared["cam0_t"] = now
                    t0 = shared.get("cam0_fps_t")
                    n = int(shared.get("cam0_n") or 0) + 1
                    if t0 is None:
                        shared["cam0_fps_t"] = now
                        shared["cam0_n"] = 1
                    elif now - float(t0) >= 1.0:
                        shared["cam0_fps"] = n / (now - float(t0))
                        shared["cam0_n"] = 0
                        shared["cam0_fps_t"] = now
                    else:
                        shared["cam0_n"] = n
                    slot = (slot + 1) % 4
        finally:
            proc.kill()
            try:
                proc.wait(timeout=1)
            except Exception:
                pass
        time.sleep(0.05)


def aim_size(sw: int, sh: int):
    # Quarter of the live frame for the 10 s Bluetooth preview.
    dw = max(2, (sw // 2) // 2 * 2)
    dh = max(2, (sh // 2) // 2 * 2)
    return dw, dh


def shrink_nv12(src, sw: int, sh: int, dw: int, dh: int):
    if not isinstance(src, (bytes, bytearray)):
        src = bytes(src)
    ysz = sw * sh
    if len(src) < ysz + ysz // 2:
        return None
    uv = src[ysz:]
    out = bytearray(dw * dh * 3 // 2)
    for oy in range(dh):
        srow = (oy * sh // dh) * sw
        drow = oy * dw
        for ox in range(dw):
            out[drow + ox] = src[srow + (ox * sw // dw)]
    suw, suh = sw // 2, sh // 2
    duw, duh = dw // 2, dh // 2
    base = dw * dh
    for oy in range(duh):
        sy = oy * suh // duh
        for ox in range(duw):
            si = (sy * suw + (ox * suw // duw)) * 2
            di = base + (oy * duw + ox) * 2
            out[di] = uv[si]
            out[di + 1] = uv[si + 1]
    return out


def _write_jpg(path: str, jpg: bytes) -> None:
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, jpg)
    finally:
        os.close(fd)
    os.replace(tmp, path)


def encode_loop(enc: TurboEnc) -> None:
    last = None
    aw, ah = aim_size(VIEW_W, VIEW_H)
    try:
        aim = TurboEnc(aw, ah, 50)
    except Exception:
        aim = None
    aim_t = 0.0
    uvc_enc = None
    uvc_wh = None
    while True:
        frame = shared.get("cam0")
        if frame is None or frame is last:
            time.sleep(0.005)
            continue
        last = frame
        load_uvc_ctl()
        jpg = enc.encode(frame)
        if jpg:
            shared["jpg"] = jpg
            shared["jpg_t"] = time.monotonic()
            try:
                _write_jpg(LIVE_JPG, jpg)
            except OSError:
                pass
        ctl = shared.get("_uvc_ctl") or {}
        tw = int(ctl.get("w") or 0)
        th = int(ctl.get("h") or 0)
        if tw > 0 and th > 0 and (tw, th) != (VIEW_W, VIEW_H):
            if uvc_wh != (tw, th):
                try:
                    uvc_enc = TurboEnc(tw, th, 70)
                except Exception:
                    uvc_enc = None
                uvc_wh = (tw, th)
            if uvc_enc is not None:
                small = shrink_nv12(frame, VIEW_W, VIEW_H, tw, th)
                if small:
                    uj = uvc_enc.encode(small)
                    if uj:
                        try:
                            _write_jpg(UVC_JPG, uj)
                        except OSError:
                            pass
        elif jpg:
            try:
                _write_jpg(UVC_JPG, jpg)
            except OSError:
                pass
        if aim is None or not os.path.exists(AIM_FLAG):
            continue
        now = time.monotonic()
        if now - aim_t < 0.45:
            continue
        aim_t = now
        small = shrink_nv12(frame, VIEW_W, VIEW_H, aw, ah)
        if not small:
            continue
        aim_jpg = aim.encode(small)
        if not aim_jpg or len(aim_jpg) > 96000:
            continue
        try:
            _write_jpg(AIM_JPG, aim_jpg)
        except OSError:
            pass


def _ps_has(name: str) -> bool:
    try:
        out = subprocess.check_output(["ps"], text=True, timeout=3)
    except Exception:
        return False
    return name in out


def ensure_companions() -> None:
    env = os.environ.copy()
    env["PATH"] = "/oem/usr/bin:/usr/sbin:/sbin:/usr/bin:/bin:" + env.get("PATH", "")
    env["LD_LIBRARY_PATH"] = "/oem/usr/lib:/oem/lib:" + env.get("LD_LIBRARY_PATH", "")
    if (
        not AM
        and not _ps_has("rkaiq_3A_server")
        and os.path.isfile("/userdata/camevision-aiq.sh")
    ):
        subprocess.Popen(
            ["/bin/sh", "/userdata/camevision-aiq.sh"],
            stdin=subprocess.DEVNULL,
            stdout=open("/userdata/aiq-boot.log", "ab"),
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
    if AM:
        set_live_30fps()
    if not _ps_has("single_imu_hud") and os.path.isfile("/userdata/single_imu_hud.py"):
        env["TZ"] = "UTC-2"
        subprocess.Popen(
            ["/usr/bin/python3", "/userdata/single_imu_hud.py"],
            stdin=subprocess.DEVNULL,
            stdout=open("/tmp/single-imu.log", "ab"),
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )


def companion_loop() -> None:
    while True:
        try:
            ensure_companions()
        except Exception as exc:
            print("companion", exc, flush=True)
        time.sleep(3)


def send(conn: socket.socket, body: bytes, ctype: str) -> None:
    conn.sendall(
        b"HTTP/1.1 200 OK\r\n"
        b"Cache-Control: no-store\r\n"
        b"Access-Control-Allow-Origin: *\r\n"
        + f"Content-Type: {ctype}\r\nContent-Length: {len(body)}\r\n\r\n".encode()
        + body
    )


def send_mjpeg(conn: socket.socket) -> None:
    conn.sendall(
        b"HTTP/1.1 200 OK\r\nCache-Control: no-cache\r\n"
        b"Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n"
    )
    last = b""
    while True:
        jpg = shared.get("jpg") or b""
        if jpg and jpg is not last:
            last = jpg
            conn.sendall(
                b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                + str(len(jpg)).encode()
                + b"\r\n\r\n"
                + jpg
                + b"\r\n"
            )
        time.sleep(0.008)


def handle(conn: socket.socket) -> None:
    try:
        req = conn.recv(2048)
        line = req.split(b"\r\n", 1)[0]
        parts = line.split()
        path = parts[1] if len(parts) >= 2 else b"/"
        if path in (b"/", b"/index.html"):
            send(conn, PAGE, "text/html; charset=utf-8")
            return
        if path == b"/brand.png":
            if os.path.isfile(LOGO):
                send(conn, open(LOGO, "rb").read(), "image/png")
            else:
                send(conn, b"", "image/png")
            return
        if path == b"/ov0":
            send_mjpeg(conn)
            return
        if path == b"/snap0":
            jpg = shared.get("jpg") or b""
            send(conn, jpg, "image/jpeg")
            return
        if path == b"/stat":
            import json

            body = json.dumps(
                {
                    "dev": DEV,
                    "w": VIEW_W,
                    "h": VIEW_H,
                    "cam0_fps": round(float(shared.get("cam0_fps") or 0), 2),
                    "jpg": bool(shared.get("jpg")),
                    "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "fmt": "BG10" if AM else "NV12",
                    "sku": "mira220" if AM else "sc233hgs",
                    "uvc": shared.get("_uvc_ctl") or {},
                }
            ).encode()
            send(conn, body, "application/json")
            return
        if path == b"/imu":
            try:
                with urllib.request.urlopen(IMU_URL, timeout=0.4) as r:
                    send(conn, r.read(), "application/json")
                    return
            except Exception:
                send(conn, b"{}", "application/json")
                return
        send(conn, b"not found", "text/plain")
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def publish_record_geom() -> None:
    fps = int(round(float(shared.get("cam0_fps") or 30)))
    if fps < 1 or fps > 120:
        fps = 30
    text = "%d %d %d\n" % (VIEW_W, VIEW_H, fps)
    try:
        tmp = RECORD_GEOM + ".tmp"
        with open(tmp, "w") as fh:
            fh.write(text)
        os.replace(tmp, RECORD_GEOM)
    except OSError:
        pass


def record_pump() -> None:
    """While a recording is on, write every full-resolution NV12 frame to the fifo."""
    fifo = None
    last = None
    while True:
        if not os.path.exists(RECORD_FLAG):
            if fifo is not None:
                try:
                    fifo.close()
                except OSError:
                    pass
                fifo = None
            last = None
            time.sleep(0.05)
            continue
        publish_record_geom()
        frame = shared.get("cam0")
        if frame is None or frame is last:
            time.sleep(0.002)
            continue
        if fifo is None:
            try:
                fifo = open(RECORD_FIFO, "wb", buffering=0)
            except OSError:
                time.sleep(0.05)
                continue
        try:
            payload = bytes(frame)
            if len(payload) != VIEW_FRAME:
                last = frame
                continue
            fifo.write(payload)
            last = frame
        except OSError:
            try:
                fifo.close()
            except OSError:
                pass
            fifo = None
            last = None


def serve() -> None:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", PORT))
    sock.listen(16)
    print(
        f"single live :{PORT} {DEV} view {VIEW_W}x{VIEW_H} cap {CAM_W}x{CAM_H}@{CAP_FPS}",
        flush=True,
    )
    while True:
        conn, _ = sock.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


def apply_sensor_180() -> None:
    if AM:
        return
    # Product 180 is sensor hflip+vflip, not Ego CSS. Set once, never in the grab loop.
    subprocess.run(
        [
            "v4l2-ctl",
            "-d",
            "/dev/v4l-subdev4",
            "--set-ctrl=horizontal_flip=1",
            "--set-ctrl=vertical_flip=1",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=3,
    )


def main() -> int:
    os.environ.setdefault("TZ", "UTC-2")
    try:
        time.tzset()
    except Exception:
        pass
    if AM:
        for p in ("/userdata/pylib", "/userdata"):
            if p not in sys.path and os.path.isdir(p):
                sys.path.insert(0, p)
    apply_sensor_180()
    ensure_companions()
    threading.Thread(target=companion_loop, daemon=True).start()
    threading.Thread(target=grab, daemon=True).start()
    threading.Thread(target=record_pump, daemon=True).start()
    try:
        enc = TurboEnc(VIEW_W, VIEW_H, 70)
        threading.Thread(target=encode_loop, args=(enc,), daemon=True).start()
    except Exception as exc:
        print("jpeg encoder", exc, flush=True)
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
