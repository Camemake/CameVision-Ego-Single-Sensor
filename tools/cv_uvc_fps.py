"""Count Camemake UVC frames for 2 seconds."""
import time
import cv2

W, H = 1400, 1600
cap = cv2.VideoCapture(1, cv2.CAP_MSMF)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
cap.set(cv2.CAP_PROP_FPS, 60)
# Warm up so open/probe is not counted.
for _ in range(6):
    cap.read()
t0 = time.perf_counter()
n = 0
size = None
while time.perf_counter() - t0 < 2.0:
    ok, frame = cap.read()
    if not ok or frame is None:
        continue
    n += 1
    size = (frame.shape[1], frame.shape[0])
dt = time.perf_counter() - t0
cap.release()
print("frames", n, "sec", round(dt, 3), "fps", round(n / dt, 1), "size", size)
