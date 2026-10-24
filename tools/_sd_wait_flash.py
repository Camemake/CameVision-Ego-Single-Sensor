#!/usr/bin/env python3
import socket
import subprocess
import sys
import time
from pathlib import Path

HOST = "192.168.1.72"
TN = str(Path(__file__).resolve().parent / "cv_tn.py")


def up(timeout=1.0):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((HOST, 2323))
        s.close()
        return True
    except Exception:
        return False


def tn(cmd, wait=8.0):
    return subprocess.check_output(
        [sys.executable, TN, "--wait", str(wait), cmd],
        text=True,
        errors="replace",
    )


print("waiting for", HOST, flush=True)
for i in range(240):
    if up():
        print("up after", i, flush=True)
        break
    time.sleep(5)
else:
    print("TIMEOUT", flush=True)
    sys.exit(2)

time.sleep(3)
print(tn("echo BACK; cat /sys/block/mmcblk1/size 2>/dev/null; ip -4 addr show wlan0 | head -3"), flush=True)
print("FLASH", flush=True)
print(
    tn(
        "wget -q -O /tmp/_sd_reflash.sh http://192.168.1.44:18766/_sd_reflash.sh; sh /tmp/_sd_reflash.sh",
        50,
    ),
    flush=True,
)
print("wait reboot", flush=True)
time.sleep(8)
for i in range(90):
    if up():
        print("rebooted", i, flush=True)
        break
    time.sleep(4)
else:
    print("NO_REBOOT_UP", flush=True)
    sys.exit(3)
time.sleep(4)
print(
    tn(
        "echo ---SD---; cat /sys/class/mmc_host/mmc1/mmc1:0001/type 2>/dev/null; "
        "cat /sys/class/mmc_host/mmc1/mmc1:0001/ocr 2>/dev/null; "
        "cat /sys/block/mmcblk1/size 2>/dev/null; "
        "hexdump -C /dev/mmcblk1 -n 64; "
        "hexdump -C /dev/mmcblk1 -s 16384 -n 64; "
        "df -h /mnt/sdcard 2>/dev/null; echo ---END---",
        12,
    ),
    flush=True,
)
