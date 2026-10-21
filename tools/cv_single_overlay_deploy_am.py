#!/usr/bin/env python3
"""Install the CameVision Mono / MIRA220 overlay over ADB.

One camera, one IMU. Does not flash partitions. Does not touch Ego.
USB stays ADB.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import (  # noqa: E402
    GEN1_SERIAL,
    adb_exe,
    current_restore,
    first_dir,
    first_file,
    overlay_dir,
    repo_root,
)
from cv_single_paths_am import (  # noqa: E402
    IQ_NAME_AM,
    MODULE,
    VIDEO_DEV_AM,
    am_module,
    boot_img_am,
    boot_ok_am,
)

ADB = adb_exe()
ROOT = repo_root()
OV = overlay_dir()
CUR = current_restore()


def serial() -> str:
    r = subprocess.run([ADB, "devices"], capture_output=True, text=True)
    found = []
    for line in (r.stdout or "").splitlines():
        if "\tdevice" not in line:
            continue
        s = line.split()[0]
        if s == GEN1_SERIAL:
            continue
        found.append(s)
    if not found:
        raise SystemExit("no ADB (gen1 0558fa189447bc45 is blocked)")
    return found[0]


def adb(s: str, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    r = subprocess.run([ADB, "-s", s, *args], capture_output=True, timeout=timeout)
    text = ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")
    if text.strip():
        print(text, end="" if text.endswith("\n") else "\n", flush=True)
    if r.returncode != 0:
        raise SystemExit(f"adb {args} failed ({r.returncode})")
    return r


def push(s: str, src: Path, dst: str, timeout: int = 60) -> None:
    print(f"push {src} -> {dst}", flush=True)
    adb(s, "push", str(src), dst, timeout=timeout)


def push_dir(s: str, src: Path, dst: str) -> None:
    adb(s, "shell", f"mkdir -p {dst}")
    print(f"push {src}/. -> {dst}", flush=True)
    adb(s, "push", str(src) + "/.", dst, timeout=180)


def _module_names(s: str) -> str:
    r = subprocess.run(
        [
            ADB,
            "-s",
            s,
            "shell",
            "for p in "
            "/proc/device-tree/i2c@21120000/mira220@54/rockchip,camera-module-name "
            "/proc/device-tree/i2c@21120000/sc233hgs@30/rockchip,camera-module-name "
            "/proc/device-tree/i2c@21120000/sc233hgs@30/compatible "
            "/proc/device-tree/i2c-gpio-cam1/mira220@54/rockchip,camera-module-name; do "
            "if [ -f \"$p\" ]; then tr -d '\\000' <\"$p\"; echo; fi; done; "
            "ls /sys/bus/i2c/devices 2>/dev/null; echo",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    return r.stdout or ""


def ensure_am_dtb(s: str) -> str:
    names = _module_names(s)
    print("camera-module-name", names.replace("\n", " ").strip(), flush=True)
    if MODULE in names:
        return s
    img = boot_img_am()
    if img is None or not boot_ok_am(img.read_bytes()):
        raise SystemExit("DTB is not MIRA220 AM and no AM boot FIT is in this package")
    print(f"=== DTB not AM — rewriting boot from {img} ===", flush=True)
    adb(s, "push", str(img), "/userdata/camevision_boot_single_am.img", timeout=180)
    adb(
        s,
        "shell",
        "dd if=/userdata/camevision_boot_single_am.img of=/dev/mmcblk0p4 bs=1M conv=fsync; sync; echo DD_OK",
        timeout=180,
    )
    subprocess.run([ADB, "-s", s, "reboot"], capture_output=True, timeout=20)
    t0 = time.time()
    while time.time() - t0 < 120:
        time.sleep(3)
        listing = subprocess.run([ADB, "devices"], capture_output=True, text=True).stdout
        if s in listing and "device" in listing:
            names = _module_names(s)
            if MODULE in names:
                print("camera-module-name after rewrite", names.replace("\n", " ").strip(), flush=True)
                return s
    raise SystemExit("board did not return with camevision-mira220")


def deploy(s: str, pylib: bool = True) -> None:
    s = ensure_am_dtb(s)
    tools = ROOT / "tools"
    files = [
        (tools / "single_live.py", "/userdata/single_live.py"),
        (tools / "libsingle_color.so", "/userdata/libsingle_color.so"),
        (tools / "single_imu_hud.py", "/userdata/single_imu_hud.py"),
        (tools / "camevision-single.sh", "/userdata/camevision-single.sh"),
        (tools / "S99camevision-single", "/userdata/S99camevision-single"),
        (tools / "S10mira220", "/userdata/S10mira220"),
        (tools / "S11hwclock", "/userdata/S11hwclock"),
        (tools / "camemake-logo.png", "/userdata/camemake-logo.png"),
        (first_file(tools / "camevision-wifi.sh", OV / "camevision-wifi.sh", CUR / "overlay" / "camevision-wifi.sh"), "/userdata/camevision-wifi.sh"),
        (first_file(tools / "wpa_camevision.conf", OV / "wpa_camevision.conf", CUR / "overlay" / "wpa_camevision.conf"), "/userdata/wpa_camevision.conf"),
        (first_file(tools / "camevision-hw.sh", OV / "camevision-hw.sh", CUR / "overlay" / "camevision-hw.sh"), "/userdata/camevision-hw.sh"),
        (first_file(tools / "camevision-led.sh", OV / "camevision-led.sh", CUR / "overlay" / "camevision-led.sh"), "/userdata/camevision-led.sh"),
        (first_file(OV / "S50usbdevice", CUR / "overlay" / "S50usbdevice"), "/userdata/S50usbdevice"),
        (first_file(OV / "S99camevision", tools / "S99camevision-single"), "/userdata/S99camevision"),
    ]
    for src, dst in files:
        if src is not None and src.is_file():
            push(s, src, dst)

    for ko in ("mira220.ko", "miralink.ko", "ciflate.ko", "clkgo.ko", "mfix4.ko", "mstart.ko"):
        src = am_module(ko)
        if src is None:
            raise SystemExit(f"missing AM module {ko}")
        push(s, src, f"/userdata/{ko}")

    kmpp = first_file(
        OV / "kmpp-rt52.ko",
        CUR / "overlay" / "kmpp-rt52.ko",
        ROOT / "restore" / "recovery-3-20260822-uvc-wifi-rkaiq" / "overlay" / "kmpp-rt52.ko",
    )
    if kmpp is not None:
        push(s, kmpp, "/userdata/kmpp-rt52.ko", timeout=60)

    iq = first_file(
        tools / "iqfiles" / IQ_NAME_AM,
        ROOT.parent / "CameVision Ego" / "tools" / "iqfiles" / IQ_NAME_AM,
    ) or am_overlay_dir_iq()
    if iq is None:
        raise SystemExit(f"missing MIRA220 IQ {IQ_NAME_AM}")
    adb(s, "shell", "mkdir -p /userdata/iqfiles")
    push(s, iq, "/userdata/iqfiles/" + IQ_NAME_AM)

    kos = first_dir(OV / "swt6621-rt52", CUR / "overlay" / "swt6621-rt52")
    fw = first_dir(OV / "swt6621_fw", CUR / "overlay" / "swt6621_fw")
    if kos is not None:
        push_dir(s, kos, "/userdata/swt6621-rt52")
    if fw is not None:
        push_dir(s, fw, "/userdata/swt6621_fw")

    adb(
        s,
        "shell",
        "printf 'am\\n' > /userdata/camevision-am.on; "
        "sed -i 's/\\r$//' /userdata/single_live.py /userdata/single_imu_hud.py "
        "/userdata/camevision-single.sh /userdata/S10mira220 "
        "/userdata/camevision-wifi.sh /userdata/camevision-hw.sh "
        "/userdata/S99camevision-single /userdata/S11hwclock /userdata/S99camevision; "
        "chmod 755 /userdata/camevision-single.sh /userdata/S10mira220 "
        "/userdata/camevision-wifi.sh /userdata/camevision-hw.sh "
        "/userdata/S99camevision-single /userdata/S11hwclock /userdata/S99camevision; "
        "rm -f /userdata/uvc-webcam.on /userdata/ego_stereo.py "
        "/userdata/ego_imu_hud.py /userdata/ego_cam_sync.py "
        "/userdata/camevision-stereo.sh /userdata/libego_stereo.so; "
        "mount -o remount,rw / 2>/dev/null; "
        "cp -f /userdata/S10mira220 /etc/init.d/S10mira220; "
        "cp -f /userdata/S99camevision-single /etc/init.d/S99camevision-single; "
        "cp -f /userdata/S99camevision-single /etc/init.d/S99camevision; "
        "if [ -f /userdata/S11hwclock ]; then cp -f /userdata/S11hwclock /etc/init.d/S11hwclock; fi; "
        "if [ -f /userdata/S50usbdevice ]; then cp -f /userdata/S50usbdevice /etc/init.d/S50usbdevice; fi; "
        "cp -f /userdata/mira220.ko /userdata/miralink.ko /userdata/ciflate.ko "
        "/userdata/clkgo.ko /userdata/mfix4.ko /userdata/mstart.ko /lib/; "
        "chmod 644 /lib/mira220.ko /lib/miralink.ko /lib/ciflate.ko "
        "/lib/clkgo.ko /lib/mfix4.ko /lib/mstart.ko; "
        "chmod 755 /etc/init.d/S10mira220 /etc/init.d/S99camevision-single "
        "/etc/init.d/S99camevision /etc/init.d/S11hwclock /etc/init.d/S50usbdevice 2>/dev/null; "
        "printf '%s\\n' '#!/bin/sh' 'exit 0' > /etc/init.d/S99ego-stereo; "
        "chmod 755 /etc/init.d/S99ego-stereo; "
        "mount -o remount,ro / 2>/dev/null; "
        "sync",
        timeout=40,
    )

    if pylib:
        wheels = first_dir(ROOT / "build" / "wheels", ROOT.parent / "CameVision Ego" / "build" / "wheels")
        extract = first_file(
            tools / "cv_ego_extract_pylib.py",
            ROOT.parent / "CameVision Ego" / "tools" / "cv_ego_extract_pylib.py",
        )
        if wheels is not None and extract is not None:
            adb(s, "shell", "mkdir -p /userdata/wheels /userdata/pylib")
            for w in sorted(wheels.glob("*.whl")):
                name = w.name.lower()
                if name.startswith("numpy-") or name.startswith("opencv_python_headless-4."):
                    push(s, w, "/userdata/wheels/" + w.name, timeout=180)
            push(s, extract, "/userdata/cv_ego_extract_pylib.py")
            adb(
                s,
                "shell",
                "sed -i 's/\\r$//' /userdata/cv_ego_extract_pylib.py; "
                "python3 /userdata/cv_ego_extract_pylib.py",
                timeout=300,
            )

    print("=== start AM CSI + live page ===", flush=True)
    adb(
        s,
        "shell",
        "killall python3 v4l2-ctl 2>/dev/null; sleep 1; "
        "sh /userdata/S10mira220; "
        "export PYTHONPATH=/userdata/pylib; "
        "sh /userdata/camevision-single.sh",
        timeout=90,
    )
    time.sleep(3)
    check = subprocess.run(
        [
            ADB,
            "-s",
            s,
            "shell",
            "n=0; while [ $n -lt 25 ]; do "
            f"[ -e {VIDEO_DEV_AM} ] || true; "
            "c0=$(wget -q -O - http://127.0.0.1:8081/snap0 2>/dev/null | wc -c); "
            "echo snap $c0; "
            "if [ \"$c0\" -gt 2000 ]; then echo CAM_OK; exit 0; fi; "
            "n=$((n+1)); sleep 1; done; "
            f"ls {VIDEO_DEV_AM} /dev/video* 2>/dev/null; "
            "tail -40 /userdata/single-live.log /tmp/single-imu.log 2>/dev/null; "
            "exit 1",
        ],
        capture_output=True,
        timeout=50,
    )
    text = ((check.stdout or b"") + (check.stderr or b"")).decode("utf-8", "replace")
    if text.strip():
        print(text, end="" if text.endswith("\n") else "\n", flush=True)
    if check.returncode != 0 or "CAM_OK" not in text:
        print("WARN AM live snap is still small — page may still start", flush=True)
    else:
        print("CAM on", flush=True)
    print("OVERLAY_AM_OK", flush=True)


def am_overlay_dir_iq() -> Path | None:
    from cv_single_paths_am import am_overlay_dir, release_am

    return first_file(
        am_overlay_dir() / "iqfiles" / IQ_NAME_AM,
        release_am() / "overlay" / "iqfiles" / IQ_NAME_AM,
        release_am() / "iqfiles" / IQ_NAME_AM,
    )


def main() -> int:
    s = sys.argv[1] if len(sys.argv) > 1 else serial()
    print("serial", s, flush=True)
    deploy(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
