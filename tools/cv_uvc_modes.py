"""List Camemake MSMF modes and sample 60 / 30 / 15 fps."""
import time
import cv2

print("opencv", cv2.__version__)
backends = [cv2.CAP_MSMF]
found = []
for idx in range(0, 6):
    cap = cv2.VideoCapture(idx, cv2.CAP_MSMF)
    if not cap.isOpened():
        continue
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    found.append((idx, w, h, fps))
    print("cam", idx, "open", w, h, "fps", fps)
    for prop, name in (
        (cv2.CAP_PROP_BRIGHTNESS, "brightness"),
        (cv2.CAP_PROP_CONTRAST, "contrast"),
        (cv2.CAP_PROP_SATURATION, "saturation"),
        (cv2.CAP_PROP_HUE, "hue"),
        (cv2.CAP_PROP_GAIN, "gain"),
        (cv2.CAP_PROP_EXPOSURE, "exposure"),
        (cv2.CAP_PROP_SHARPNESS, "sharpness"),
        (cv2.CAP_PROP_GAMMA, "gamma"),
        (cv2.CAP_PROP_AUTO_EXPOSURE, "ae"),
        (cv2.CAP_PROP_AUTO_WB, "awb"),
        (cv2.CAP_PROP_WB_TEMPERATURE, "wb"),
        (cv2.CAP_PROP_BACKLIGHT, "backlight"),
    ):
        try:
            print(" ", name, cap.get(prop))
        except Exception as exc:
            print(" ", name, exc)
    cap.release()
print("found", found)

idx = 1 if any(i == 1 for i, *_ in found) else (found[0][0] if found else 1)
sizes = ((1400, 1600), (1050, 1200), (700, 800), (350, 400))
rates = (60, 30, 15)
for w, h in sizes:
    for rate in rates:
        cap = cv2.VideoCapture(idx, cv2.CAP_MSMF)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_FPS, rate)
        got_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        got_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        got_fps = cap.get(cv2.CAP_PROP_FPS)
        for _ in range(4):
            cap.read()
        t0 = time.perf_counter()
        n = 0
        size = None
        while time.perf_counter() - t0 < 1.2:
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            n += 1
            size = (frame.shape[1], frame.shape[0])
        dt = time.perf_counter() - t0
        cap.release()
        print(
            "mode want %dx%d@%d got %dx%d@%.1f meas %.1f size %s"
            % (w, h, rate, got_w, got_h, got_fps, (n / dt) if dt else 0, size)
        )
