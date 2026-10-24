#!/usr/bin/env python3
"""Push the UVC gadget, then switch USB to composite ADB+UVC."""
from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import GEN1_SERIAL, adb_exe  # noqa: E402

ROOT = Path(__file__).resolve().parent
FILES = {
    ROOT / "camevision-uvc-gadget.sh": "/userdata/camevision-uvc-gadget.sh",
    ROOT / "camevision-uvc-start.sh": "/userdata/camevision-uvc-start.sh",
    ROOT / "camevision-uvc-stop.sh": "/userdata/camevision-uvc-stop.sh",
    ROOT / "camevision-uvc-bridge.py": "/userdata/camevision-uvc-bridge.py",
    ROOT / "single_live.py": "/userdata/single_live.py",
}
ADB = adb_exe()


def adb(serial: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [ADB, "-s", serial, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def pick_serial() -> str:
    r = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=10)
    found = []
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            if parts[0] != GEN1_SERIAL:
                found.append(parts[0])
    if not found:
        raise SystemExit("no ADB board (gen1 skipped)")
    return found[0]


def wait_serial(prefer: str, seconds: int = 40) -> str | None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        r = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=10)
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device" and parts[0] != GEN1_SERIAL:
                return parts[0]
        time.sleep(1)
    return None


def push_unix(serial: str, src: Path, dst: str) -> None:
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", newline="\n") as tmp:
        tmp.write(text)
        name = tmp.name
    r = adb(serial, "push", name, dst, timeout=60)
    Path(name).unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout or "push failed")
    print("push", dst)


def telnet_ok(host: str, port: int = 2323) -> bool:
    try:
        s = socket.create_connection((host, port), 4)
        s.settimeout(2)
        try:
            s.recv(256)
        except Exception:
            pass
        s.send(b"echo UVC_TELNET_OK\n")
        time.sleep(0.4)
        out = s.recv(1024).decode("utf-8", "replace")
        s.close()
        return "UVC_TELNET_OK" in out
    except OSError:
        return False


def main() -> int:
    s = pick_serial()
    print("serial", s)
    adb(s, "shell", "mount -o remount,rw /userdata")
    for src, dst in FILES.items():
        if src.is_file():
            push_unix(s, src, dst)
    adb(
        s,
        "shell",
        "chmod 755 /userdata/camevision-uvc-gadget.sh "
        "/userdata/camevision-uvc-start.sh /userdata/camevision-uvc-stop.sh "
        "/userdata/camevision-uvc-bridge.py; "
        "busybox telnetd -l /bin/sh -p 2323",
    )
    wifi = adb(
        s,
        "shell",
        "ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}'",
        timeout=15,
    )
    ip = ""
    for line in (wifi.stdout or "").splitlines():
        if "/" in line and not line.startswith("127."):
            ip = line.split("/")[0].strip()
            break
    if ip and telnet_ok(ip):
        print("TELNET_OK", ip + ":2323")
    else:
        print("wlan0", ip or "DOWN", "— composite keeps ADB")

    print("switching USB to ADB+UVC composite")
    subprocess.Popen(
        [
            ADB,
            "-s",
            s,
            "shell",
            "setsid /bin/sh /userdata/camevision-uvc-start.sh "
            "</dev/null >/userdata/cv-uvc-start.log 2>&1",
        ]
    )
    time.sleep(2)
    back = wait_serial(s, 35)
    if not back:
        print("ADB not back yet — try unplug/replug USB-C")
        return 0
    print("adb", back)
    st = adb(
        back,
        "shell",
        "echo pid=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct); "
        "echo prod=$(cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product); "
        "echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC); "
        "echo state=$(cat /sys/class/udc/21500000.usb/state); "
        "echo speed=$(cat /sys/class/udc/21500000.usb/current_speed); "
        "ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1; "
        "tail -20 /userdata/cv-uvc-start.log; "
        "tail -20 /userdata/cv-uvc-bridge.log; "
        "for v in /sys/class/video4linux/video*; do "
        "n=$(cat $v/name); echo $v $n; done | grep -iE 'gadget|uvc|camevision|dummy'",
        timeout=20,
    )
    print(st.stdout)
    print("Windows Camera: CameVision Ego Single Sensor")
    print("stop: adb shell /userdata/camevision-uvc-stop.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
