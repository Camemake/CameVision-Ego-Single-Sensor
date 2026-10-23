#!/usr/bin/env python3
"""Single-IMU HUD sampler. Discovers the LSM6 IIO pair on SPI1."""
from __future__ import annotations

import json
import os
import socket
import threading
import time
from pathlib import Path

PORT = 8083
ODR = "480"
G = 9.80665
RAD2DEG = 57.29577951308232
IIO = Path("/sys/bus/iio/devices")

lock = threading.Lock()
state = {
    "t_unix_ns": 0,
    "t_iso": "",
    "t_mono_ns": 0,
    "odr_hz": float(ODR),
    "read_hz": 0.0,
    "imu0": {},
}


def ns_realtime() -> int:
    return time.clock_gettime_ns(time.CLOCK_REALTIME)


def ns_mono() -> int:
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC)


def iso_now(ns: int) -> str:
    sec, nsec = divmod(ns, 1_000_000_000)
    tm = time.localtime(sec)
    off = -time.timezone if (not tm.tm_isdst) else -time.altzone
    sign = "+" if off >= 0 else "-"
    hh, mm = divmod(abs(off) // 60, 60)
    return time.strftime("%Y-%m-%dT%H:%M:%S", tm) + f".{nsec//1000000:03d}{sign}{hh:02d}:{mm:02d}"


def fopen(path: Path):
    return open(path, "rb", buffering=0)


def fread_int(f) -> int:
    f.seek(0)
    return int(f.read().strip() or b"0")


def discover() -> dict:
    accel = gyro = None
    if IIO.is_dir():
        for d in sorted(IIO.glob("iio:device*")):
            try:
                name = (d / "name").read_text().strip().lower()
            except OSError:
                continue
            if "lsm6" not in name and "accel" not in name and "gyro" not in name:
                continue
            if "accel" in name or (d / "in_accel_x_raw").is_file():
                accel = d
            if "gyro" in name or "anglvel" in name or (d / "in_anglvel_x_raw").is_file():
                gyro = d
    if accel is None or gyro is None:
        raise SystemExit("no LSM6 IIO accel/gyro pair")
    bus = "spi1.0"
    spi = Path("/sys/bus/spi/devices")
    if spi.is_dir():
        for p in sorted(spi.glob("spi*")):
            try:
                if any(accel.name in x.name or gyro.name in x.name for x in p.rglob("iio:device*")):
                    bus = p.name
                    break
            except OSError:
                continue
    return {"id": "imu0", "cam": 0, "bus": bus, "accel": accel, "gyro": gyro}


def disable_buffers(imu: dict) -> None:
    for d in (imu["accel"], imu["gyro"]):
        try:
            (d / "buffer" / "enable").write_text("0")
        except OSError:
            pass


def _touch(patch: dict) -> None:
    t_unix = ns_realtime()
    t_mono = ns_mono()
    patch["t_unix_ns"] = t_unix
    patch["t_iso"] = iso_now(t_unix)
    patch["t_mono_ns"] = t_mono
    with lock:
        rec = dict(state.get("imu0") or {})
        rec.update(patch)
        if "ax" in rec and "ay" in rec and "az" in rec:
            rec["a_g"] = (rec["ax"] ** 2 + rec["ay"] ** 2 + rec["az"] ** 2) ** 0.5 / G
        state["imu0"] = rec
        state["t_unix_ns"] = t_unix
        state["t_iso"] = patch["t_iso"]
        state["t_mono_ns"] = t_mono
        state["read_hz"] = rec.get("read_hz") or 0.0
        state["odr_hz"] = float(ODR)


def sample_half(imu: dict, kind: str) -> None:
    a, g = imu["accel"], imu["gyro"]
    try:
        ((a if kind == "accel" else g) / "sampling_frequency").write_text(ODR)
    except OSError:
        pass
    if kind == "accel":
        files = (
            fopen(a / "in_accel_x_raw"),
            fopen(a / "in_accel_y_raw"),
            fopen(a / "in_accel_z_raw"),
        )
        scl = float((a / "in_accel_scale").read_text())
        keys = ("ax", "ay", "az")
    else:
        files = (
            fopen(g / "in_anglvel_x_raw"),
            fopen(g / "in_anglvel_y_raw"),
            fopen(g / "in_anglvel_z_raw"),
        )
        scl = float((g / "in_anglvel_scale").read_text()) * RAD2DEG
        keys = ("gx", "gy", "gz")
    n = 0
    t0 = time.monotonic()
    hz = 0.0
    while True:
        vals = [fread_int(f) * scl for f in files]
        n += 1
        now = time.monotonic()
        if now - t0 >= 0.5:
            hz = n / (now - t0)
            n = 0
            t0 = now
        _touch(
            {
                keys[0]: vals[0],
                keys[1]: vals[1],
                keys[2]: vals[2],
                "read_hz": hz,
                "cam": imu["cam"],
                "bus": imu["bus"],
            }
        )


def handle(conn: socket.socket) -> None:
    try:
        req = conn.recv(1024)
        if b"GET /" not in req:
            return
        with lock:
            body = json.dumps(state, separators=(",", ":")).encode()
        conn.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Access-Control-Allow-Origin: *\r\n"
            b"Cache-Control: no-store\r\n"
            b"Content-Length: "
            + str(len(body)).encode()
            + b"\r\n\r\n"
            + body
        )
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
    sock.listen(8)
    print(f"imu hud :{PORT} odr={ODR}", flush=True)
    while True:
        conn, _ = sock.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


def main() -> int:
    os.environ.setdefault("TZ", "UTC-2")
    time.tzset()
    imu = discover()
    disable_buffers(imu)
    threading.Thread(target=sample_half, args=(imu, "accel"), daemon=True).start()
    threading.Thread(target=sample_half, args=(imu, "gyro"), daemon=True).start()
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
