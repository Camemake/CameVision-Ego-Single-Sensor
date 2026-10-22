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
CAP_FPS = 60
NATIVE = None


def _load_native() -> None:
    global NATIVE
    if not AM:
        return
    for path in (COLOR_SO, "/userdata/libego_stereo.so"):
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


def _i2c_wr16(bus: int, reg: int, val: int) -> None:
    fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    try:
        fcntl.ioctl(fd, I2C_SLAVE_FORCE, 0x54)
        os.write(fd, bytes([reg >> 8, reg & 0xFF, val & 0xFF, val >> 8]))
    finally:
        os.close(fd)


def _i2c_rd16(bus: int, reg: int) -> int:
    fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
    try:
        fcntl.ioctl(fd, I2C_SLAVE_FORCE, 0x54)
        os.write(fd, bytes([reg >> 8, reg & 0xFF]))
        b = os.read(fd, 2)
        return b[0] | (b[1] << 8)
    finally:
        os.close(fd)


def set_live_30fps() -> None:
    """Keep Ego AM window + exposure on the sensor.

    The mira220 driver rewrites VSTART=64 and EXP=1000 on stream-on.
    VSTART≠0 slides 64 dummy rows into the frame; after 90° CCW that is
    a bad right edge. Re-apply like Ego (after STREAMON and every few s).
    """
    if not AM:
        return
    try:
        # Full 1600×1400 active array. Same regs as Ego AM CAM0.
        _i2c_wr16(3, 0x107D, 0)
        _i2c_wr16(3, 0x200A, 0)
        _i2c_wr16(3, 0x1087, CAM_H)
        _i2c_wr16(3, 0x2008, CAM_W // 2)
        _i2c_wr16(3, 0x207D, CAM_W)
        _i2c_wr16(3, 0x100C, LIVE_EXPOSURE)
        _i2c_wr16(3, 0x1012, LIVE_VBLANK)
        _i2c_wr16(3, 0x1103, LIVE_VBLANK)
        vstart = _i2c_rd16(3, 0x107D)
        exp = _i2c_rd16(3, 0x100C)
        vblank = _i2c_rd16(3, 0x1012)
        if not shared.get("_fps30") or shared.get("_mira_vstart") != vstart:
            print(
                "mira220: exp %d vblank %d vstart %d vsize %d"
                % (exp, vblank, vstart, _i2c_rd16(3, 0x1087)),
                flush=True,
            )
            shared["_fps30"] = True
            shared["_mira_vstart"] = vstart
    except Exception as exc:
        print("mira220 fps", exc, flush=True)


_RAW_SCR = {}
_LUT_R_C = _LUT_G_C = _LUT_B_C = None


def _awb_lut_c():
    """Same 10-bit AWB LUTs as Ego AM: R×1.90 G×1.38 B×3.06, black-10."""
    global _LUT_R_C, _LUT_G_C, _LUT_B_C
    if _LUT_R_C is None:
        import numpy as np

        x = np.arange(1024, dtype=np.int16)
        u8 = np.clip((x >> 2) - 10, 0, 255).astype(np.int16)
        r = np.ascontiguousarray(np.clip(u8 * 1.90, 0, 255).astype(np.uint8))
        g = np.ascontiguousarray(np.clip(u8 * 1.38, 0, 255).astype(np.uint8))
        b = np.ascontiguousarray(np.clip(u8 * 3.06, 0, 255).astype(np.uint8))
        _LUT_R_C = (c_ubyte * 1024).from_buffer(r)
        _LUT_G_C = (c_ubyte * 1024).from_buffer(g)
        _LUT_B_C = (c_ubyte * 1024).from_buffer(b)
        shared["_awb_keep"] = (r, g, b)
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


def encode_loop(enc: TurboEnc) -> None:
    last = None
    while True:
        frame = shared.get("cam0")
        if frame is None or frame is last:
            time.sleep(0.005)
            continue
        last = frame
        jpg = enc.encode(frame)
        if jpg:
            shared["jpg"] = jpg
            shared["jpg_t"] = time.monotonic()


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
    try:
        enc = TurboEnc(VIEW_W, VIEW_H, 70)
        threading.Thread(target=encode_loop, args=(enc,), daemon=True).start()
    except Exception as exc:
        print("jpeg encoder", exc, flush=True)
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
