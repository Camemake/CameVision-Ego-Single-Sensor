#!/usr/bin/env python3
"""Restart the Camemake JPEG pump over ADB and dump its log."""
from __future__ import annotations

import subprocess
import time

SERIAL = "CV-EGO01-CAM"


def sh(cmd: str, timeout: int = 20) -> str:
    r = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return (r.stdout or "") + (r.stderr or "")


def main() -> int:
    print("=== log before ===")
    print(sh("cat /userdata/cv-uvc-bridge.log; echo ---; ls /dev/video53; cat /sys/class/video4linux/video53/name"))
    print("=== restart ===")
    print(
        sh(
            "for p in $(ps | grep camevision-uvc-bridge | grep -v grep | awk '{print $1}'); do kill -9 $p; done; "
            ": > /userdata/cv-uvc-bridge.log; "
            "setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 & "
            "echo STARTED $!"
        )
    )
    time.sleep(1.2)
    print(sh("ps | grep camevision-uvc-bridge | grep -v grep; echo ---LOG---; cat /userdata/cv-uvc-bridge.log"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
