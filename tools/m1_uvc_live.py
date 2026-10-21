#!/usr/bin/env python3
"""Live M1 UVC preview. Probes camera indexes; prefers 1920x1200 @ 60."""
from __future__ import annotations

import time

import cv2

W, H, FPS = 1920, 1200, 60


def open_cam():
    last_err = "no camera"
    for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF):
        for i in range(4):
            cap = cv2.VideoCapture(i, backend)
            if not cap.isOpened():
                cap.release()
                continue
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
            cap.set(cv2.CAP_PROP_FPS, FPS)
            ok, frame = cap.read()
            if not ok or frame is None:
                cap.release()
                last_err = f"index {i} opened but no frame"
                continue
            h, w = frame.shape[:2]
            print(f"try {i} backend={backend} {w}x{h}", flush=True)
            # Prefer the board (1920-wide) over the laptop webcam.
            if w >= 1280:
                return cap, frame, backend, i
            cap.release()
    raise SystemExit(last_err + ". Close the browser/Camera app if they hold UVC Camera.")


def main() -> int:
    cap, frame, backend, idx = open_cam()
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    req = cap.get(cv2.CAP_PROP_FPS)
    print(f"using index {idx} {w}x{h} req={req} backend={backend}", flush=True)
    win = "M1 live"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 1280, 800)
    n = 0
    t0 = time.time()
    fps = 0.0
    while True:
        ok, frame = cap.read()
        if not ok:
            print("frame lost", flush=True)
            break
        n += 1
        now = time.time()
        if now - t0 >= 1.0:
            fps = n / (now - t0)
            n = 0
            t0 = now
        cv2.putText(
            frame,
            f"{w}x{h}  {fps:.1f} fps",
            (24, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0) if fps >= 55 else (0, 180, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow(win, frame)
        if cv2.waitKey(1) & 0xFF in (27, ord("q")):
            break
    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
