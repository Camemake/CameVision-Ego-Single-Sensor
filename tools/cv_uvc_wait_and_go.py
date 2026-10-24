#!/usr/bin/env python3
"""Wait for the AM board, then start composite ADB+UVC."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import GEN1_SERIAL, adb_exe  # noqa: E402
from cv_uvc_bringup import adb, pick_serial, push_unix, wait_serial, FILES  # noqa: E402

ADB = adb_exe()


def present_usb() -> str:
    ps = (
        "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match '2207' } | "
        "Select-Object Status,Class,FriendlyName,InstanceId | Format-List"
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        timeout=20,
    )
    return r.stdout


def cameras() -> str:
    ps = (
        "Get-PnpDevice -PresentOnly -Class Camera,Image -ErrorAction SilentlyContinue | "
        "Select-Object Status,FriendlyName,InstanceId | Format-List"
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True,
        text=True,
        timeout=20,
    )
    return r.stdout


def main() -> int:
    print("waiting for ADB (power-cycle the board if USB is dark)")
    serial = None
    for i in range(180):
        try:
            serial = pick_serial()
            break
        except SystemExit:
            if i % 10 == 0:
                usb = present_usb()
                print("still waiting", i, flush=True)
                if usb.strip():
                    print(usb, flush=True)
            time.sleep(2)
    if not serial:
        print("NO_ADB after wait")
        return 1
    print("serial", serial)
    adb(serial, "shell", "mount -o remount,rw /userdata")
    for src, dst in FILES.items():
        if src.is_file():
            push_unix(serial, src, dst)
    adb(
        serial,
        "shell",
        "chmod 755 /userdata/camevision-uvc-gadget.sh "
        "/userdata/camevision-uvc-start.sh /userdata/camevision-uvc-stop.sh "
        "/userdata/camevision-uvc-bridge.py",
    )
    print("starting composite ADB+UVC")
    subprocess.Popen(
        [
            ADB,
            "-s",
            serial,
            "shell",
            "setsid /bin/sh /userdata/camevision-uvc-start.sh "
            "</dev/null >/userdata/cv-uvc-start.log 2>&1",
        ]
    )
    time.sleep(2)
    back = wait_serial(serial, 40)
    if not back:
        print("ADB not back")
        print(present_usb())
        print(cameras())
        return 2
    st = adb(
        back,
        "shell",
        "echo pid=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct); "
        "echo prod=$(cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product); "
        "echo cfg=$(ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1); "
        "echo state=$(cat /sys/class/udc/21500000.usb/state); "
        "echo speed=$(cat /sys/class/udc/21500000.usb/current_speed); "
        "tail -20 /userdata/cv-uvc-start.log; "
        "echo ===BRIDGE===; tail -20 /userdata/cv-uvc-bridge.log; "
        "echo ===NODES===; "
        "for v in /sys/class/video4linux/video*; do "
        "n=$(cat $v/name); echo $v $n; done | grep -iE 'gadget|uvc|camevision|dummy'",
        timeout=20,
    )
    print(st.stdout)
    print("===USB===")
    print(present_usb())
    print("===CAM===")
    print(cameras())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
