#!/usr/bin/env python3
"""Grab one frame from Camemake. MSMF without FOURCC matches Windows Camera."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2

OUT = Path(__file__).resolve().parent / "camemake-frame.jpg"
W, H = 1400, 1600
LAPTOP = {(1280, 720), (640, 480)}


def try_cap(src, backend, fcc, w=W, h=H) -> tuple[bool, str]:
    cap = cv2.VideoCapture(src, backend)
    if not cap.isOpened():
        return False, "not opened"
    if w:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    if fcc:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fcc))
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        return False, "no frame"
    fh, fw = frame.shape[:2]
    print(f"GOT {fw}x{fh} from {src!r} be={backend} fcc={fcc}", flush=True)
    if (fw, fh) in LAPTOP:
        cap.release()
        return False, "laptop-size"
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    cap.release()
    if not ok:
        return False, "encode"
    OUT.write_bytes(buf.tobytes())
    print("wrote", OUT, OUT.stat().st_size, flush=True)
    return True, f"{fw}x{fh}"


def main() -> int:
    # MSMF / no FOURCC is what Windows Camera uses.
    attempts = [
        ("MSMF", cv2.CAP_MSMF, 1, None, W, H),
        ("MSMF", cv2.CAP_MSMF, 1, None, 0, 0),
        ("MSMF", cv2.CAP_MSMF, 1, "MJPG", W, H),
        ("DSHOW", cv2.CAP_DSHOW, 1, "MJPG", W, H),
        ("DSHOW", cv2.CAP_DSHOW, 1, None, W, H),
        ("DSHOW", cv2.CAP_DSHOW, "Camemake", "MJPG", W, H),
    ]
    for be_name, be, src, fcc, w, h in attempts:
        print(f"try {be_name} src={src!r} fcc={fcc} {w}x{h}", flush=True)
        ok, err = try_cap(src, be, fcc, w, h)
        if ok:
            return 0
        print(" ", err, flush=True)
    print("FAIL no Camemake frames", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
