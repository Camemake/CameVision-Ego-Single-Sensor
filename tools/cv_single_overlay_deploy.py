#!/usr/bin/env python3
"""Install the CameVision Single overlay over ADB: live page, 1 IMU, Wi-Fi.

Does not flash partitions. USB stays ADB. Used after Maskrom and by
tools/cv_single_flash.py.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import (  # noqa: E402
    GEN1_SERIAL,
    IQ_NAME,
    VIDEO_DEV,
    adb_exe,
    current_restore,
    first_dir,
    first_file,
    overlay_dir,
    repo_root,
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


def push(s: str, src: Path, dst: str, timeout: int = 30) -> None:
    print(f"push {src} -> {dst}", flush=True)
    adb(s, "push", str(src), dst, timeout=timeout)


def push_dir(s: str, src: Path, dst: str) -> None:
    adb(s, "shell", f"mkdir -p {dst}")
    print(f"push {src}/. -> {dst}", flush=True)
    adb(s, "push", str(src) + "/.", dst, timeout=180)


def deploy(s: str) -> None:
    tools = ROOT / "tools"
    files = [
        (tools / "single_live.py", "/userdata/single_live.py"),
        (tools / "camevision-uvc-gadget.sh", "/userdata/camevision-uvc-gadget.sh"),
        (tools / "camevision-uvc-start.sh", "/userdata/camevision-uvc-start.sh"),
        (tools / "camevision-uvc-stop.sh", "/userdata/camevision-uvc-stop.sh"),
        (tools / "camevision-uvc-bridge.py", "/userdata/camevision-uvc-bridge.py"),
        (tools / "single_imu_hud.py", "/userdata/single_imu_hud.py"),
        (tools / "camevision_agent.py", "/userdata/camevision_agent.py"),
        (tools / "camevision_ble.py", "/userdata/camevision_ble.py"),
        (tools / "camevision-single.sh", "/userdata/camevision-single.sh"),
        (tools / "S99camevision-single", "/userdata/S99camevision-single"),
        (tools / "S11hwclock", "/userdata/S11hwclock"),
        (tools / "camemake-logo.png", "/userdata/camemake-logo.png"),
        (first_file(tools / "camevision-aiq.sh", OV / "camevision-aiq.sh", CUR / "overlay" / "camevision-aiq.sh"), "/userdata/camevision-aiq.sh"),
        (first_file(tools / "camevision-wifi.sh", OV / "camevision-wifi.sh", CUR / "overlay" / "camevision-wifi.sh"), "/userdata/camevision-wifi.sh"),
        (first_file(tools / "wpa_camevision.conf", OV / "wpa_camevision.conf", CUR / "overlay" / "wpa_camevision.conf"), "/userdata/wpa_camevision.conf"),
        (first_file(tools / "camevision-hw.sh", OV / "camevision-hw.sh", CUR / "overlay" / "camevision-hw.sh"), "/userdata/camevision-hw.sh"),
        (first_file(tools / "camevision-led.sh", OV / "camevision-led.sh", CUR / "overlay" / "camevision-led.sh"), "/userdata/camevision-led.sh"),
        (first_file(tools / "camevision-imu.sh", OV / "camevision-imu.sh", CUR / "overlay" / "camevision-imu.sh"), "/userdata/camevision-imu.sh"),
        (first_file(tools / "camevision-diag.sh", OV / "camevision-diag.sh", CUR / "overlay" / "camevision-diag.sh"), "/userdata/camevision-diag.sh"),
        (first_file(OV / "S50usbdevice", CUR / "overlay" / "S50usbdevice"), "/userdata/S50usbdevice"),
        (first_file(OV / "S99camevision", tools / "S99camevision-single"), "/userdata/S99camevision"),
    ]
    for src, dst in files:
        if src is not None and src.is_file():
            push(s, src, dst)

    kmpp = first_file(
        OV / "kmpp-rt52.ko",
        CUR / "overlay" / "kmpp-rt52.ko",
        ROOT / "restore" / "recovery-3-20260822-uvc-wifi-rkaiq" / "overlay" / "kmpp-rt52.ko",
        ROOT / "restore" / "recovery-2-20260821-adb-stream" / "overlay" / "kmpp-rt52.ko",
    )
    if kmpp is not None:
        push(s, kmpp, "/userdata/kmpp-rt52.ko", timeout=60)

    iq = first_file(
        tools / "iqfiles" / IQ_NAME,
        OV / "iqfiles" / IQ_NAME,
        CUR / "overlay" / "iqfiles" / IQ_NAME,
    )
    if iq is None:
        raise SystemExit(f"missing SC233HGS IQ {IQ_NAME}")
    adb(s, "shell", "mkdir -p /userdata/iqfiles")
    push(s, iq, "/userdata/iqfiles/" + IQ_NAME)

    kos = first_dir(OV / "swt6621-rt52", CUR / "overlay" / "swt6621-rt52")
    fw = first_dir(OV / "swt6621_fw", CUR / "overlay" / "swt6621_fw")
    if kos is not None:
        push_dir(s, kos, "/userdata/swt6621-rt52")
    else:
        print("WARN Wi-Fi modules not in this package — imaging still installs", flush=True)
    if fw is not None:
        push_dir(s, fw, "/userdata/swt6621_fw")

    adb(
        s,
        "shell",
        "sed -i 's/\\r$//' /userdata/single_live.py /userdata/single_imu_hud.py "
        "/userdata/camevision_agent.py /userdata/camevision_ble.py "
        "/userdata/camevision-single.sh /userdata/camevision-aiq.sh "
        "/userdata/camevision-wifi.sh /userdata/camevision-hw.sh "
        "/userdata/camevision-led.sh /userdata/camevision-imu.sh "
        "/userdata/camevision-diag.sh /userdata/wpa_camevision.conf "
        "/userdata/S99camevision-single /userdata/S11hwclock /userdata/S99camevision "
        "/userdata/camevision-uvc-gadget.sh /userdata/camevision-uvc-start.sh "
        "/userdata/camevision-uvc-stop.sh /userdata/camevision-uvc-bridge.py; "
        "chmod 755 /userdata/camevision-single.sh /userdata/camevision-aiq.sh "
        "/userdata/camevision-wifi.sh /userdata/camevision-hw.sh "
        "/userdata/camevision-led.sh /userdata/camevision-imu.sh "
        "/userdata/camevision-diag.sh /userdata/S99camevision-single "
        "/userdata/S11hwclock /userdata/S99camevision "
        "/userdata/camevision-uvc-gadget.sh /userdata/camevision-uvc-start.sh "
        "/userdata/camevision-uvc-stop.sh /userdata/camevision-uvc-bridge.py; "
        "rm -f /userdata/uvc-webcam.on /userdata/ego_stereo.py "
        "/userdata/ego_imu_hud.py /userdata/ego_cam_sync.py "
        "/userdata/camevision-stereo.sh /userdata/libego_stereo.so; "
        "mount -o remount,rw / 2>/dev/null; "
        "cp -f /userdata/S99camevision-single /etc/init.d/S99camevision-single; "
        "cp -f /userdata/S99camevision-single /etc/init.d/S99camevision; "
        "if [ -f /userdata/S11hwclock ]; then cp -f /userdata/S11hwclock /etc/init.d/S11hwclock; fi; "
        "if [ -f /userdata/S50usbdevice ]; then cp -f /userdata/S50usbdevice /etc/init.d/S50usbdevice; fi; "
        "chmod 755 /etc/init.d/S99camevision-single /etc/init.d/S99camevision "
        "/etc/init.d/S11hwclock /etc/init.d/S50usbdevice 2>/dev/null; "
        "printf '%s\\n' '#!/bin/sh' 'exit 0' > /etc/init.d/S99ego-stereo; "
        "chmod 755 /etc/init.d/S99ego-stereo; "
        "mount -o remount,ro / 2>/dev/null; "
        "if [ -f /userdata/iqfiles/" + IQ_NAME + " ]; then "
        "mount -o remount,rw /oem 2>/dev/null; "
        "cp -f /userdata/iqfiles/" + IQ_NAME + " /oem/usr/share/iqfiles/" + IQ_NAME + "; "
        "ln -sfn " + IQ_NAME + " /oem/usr/share/iqfiles/sc233hgs_default_default.json; fi",
        timeout=40,
    )

    print("=== start IQ / 3A ===", flush=True)
    adb(s, "shell", "sh /userdata/camevision-aiq.sh", timeout=90)

    print("=== start live page ===", flush=True)
    adb(
        s,
        "shell",
        "kill $(ps | awk '/single_live.py|ego_stereo.py/ && !/awk/ {print $1}') 2>/dev/null; "
        "killall v4l2-ctl 2>/dev/null; sleep 1; sh /userdata/camevision-single.sh",
        timeout=90,
    )
    check = subprocess.run(
        [
            ADB,
            "-s",
            s,
            "shell",
            "n=0; while [ $n -lt 30 ]; do "
            f"[ -e {VIDEO_DEV} ] && "
            "grep -q 'AWBGAIN    ON' /proc/rkisp* 2>/dev/null && exit 0; "
            "n=$((n+1)); sleep 1; done; "
            f"ls {VIDEO_DEV} /proc/rkisp* 2>/dev/null; exit 1",
        ],
        capture_output=True,
        timeout=45,
    )
    text = ((check.stdout or b"") + (check.stderr or b"")).decode("utf-8", "replace")
    if text.strip():
        print(text, end="" if text.endswith("\n") else "\n", flush=True)
    if check.returncode != 0:
        print("WARN ISP did not report AWBGAIN yet — live page may still start", flush=True)
    else:
        print("ISP on", flush=True)

    live = subprocess.run(
        [
            ADB,
            "-s",
            s,
            "shell",
            "n=0; while [ $n -lt 25 ]; do "
            "netstat -lnt 2>/dev/null | grep -q 8081 && echo LIVE_OK && exit 0; "
            "ss -lnt 2>/dev/null | grep -q 8081 && echo LIVE_OK && exit 0; "
            "n=$((n+1)); sleep 1; done; exit 1",
        ],
        capture_output=True,
        timeout=40,
    )
    live_text = ((live.stdout or b"") + (live.stderr or b"")).decode("utf-8", "replace")
    if live_text.strip():
        print(live_text, end="" if live_text.endswith("\n") else "\n", flush=True)
    if live.returncode != 0:
        print("WARN :8081 is not listening yet — use Open after the board finishes boot", flush=True)
    else:
        print("LIVE on", flush=True)
    print("OVERLAY_OK", flush=True)


def main() -> int:
    s = sys.argv[1] if len(sys.argv) > 1 else serial()
    print("serial", s, flush=True)
    deploy(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
