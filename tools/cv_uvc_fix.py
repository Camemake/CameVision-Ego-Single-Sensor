#!/usr/bin/env python3
"""Push Camemake scripts over ADB, neutralize usbdevice, bind UVC+ADB."""
from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cv_tn import HOST, PORT, run as tn

ADB = "adb"
SERIAL = "e4feca993701b30c"
FILES = {
    HERE / "g.sh": "/userdata/g.sh",
    HERE / "camevision-uvc-hold.sh": "/userdata/camevision-uvc-hold.sh",
    HERE / "camevision-uvc-bridge.py": "/userdata/camevision-uvc-bridge.py",
}


def adb(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [ADB, "-s", SERIAL, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def push_unix(src: Path, dst: str) -> None:
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", newline="\n") as tmp:
        tmp.write(text)
        name = tmp.name
    r = adb("push", name, dst, timeout=60)
    Path(name).unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout or "push failed %s" % dst)
    print("push", dst, len(text))


def main() -> int:
    print("=== push ===")
    for src, dst in FILES.items():
        push_unix(src, dst)
    print(
        adb(
            "shell",
            "busybox telnetd -l /bin/sh -p 2323; "
            "printf '%s\\n' '#!/bin/sh' 'exit 0' > /tmp/usbdevice.noop; "
            "chmod 755 /tmp/usbdevice.noop /userdata/g.sh /userdata/camevision-uvc-hold.sh; "
            "mount --bind /tmp/usbdevice.noop /usr/bin/usbdevice 2>/dev/null || true; "
            "grep -q USB_FORCE_CHANGED /tmp/.usb_config || echo USB_FORCE_CHANGED >> /tmp/.usb_config; "
            "touch /userdata/camevision-am.on; "
            "head -1 /userdata/g.sh; wc -c /userdata/g.sh /userdata/camevision-uvc-bridge.py; "
            "ip -4 addr show wlan0 | grep inet",
        ).stdout
    )
    time.sleep(0.3)
    socket.create_connection((HOST, PORT), 5).close()
    print("=== bind via wifi ===")
    out = tn("trap '' HUP; /bin/sh /userdata/g.sh; echo GO_DONE", wait=18)
    print(out)
    time.sleep(2)
    out = tn(
        "echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct); "
        "echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC); "
        "echo STATE=$(cat /sys/class/udc/21500000.usb/state); "
        "echo PRODUCT=$(cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product); "
        "readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1; "
        "readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2; "
        "ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/; "
        "ps | grep camevision-uvc-bridge | grep -v grep; "
        "tail -25 /userdata/cv-uvc-bridge.log",
        wait=5,
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
