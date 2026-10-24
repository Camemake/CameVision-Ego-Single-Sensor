#!/usr/bin/env python3
"""Rebuild working SD boot (no 16G lie) and write it over ADB."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADB = str(ROOT / "host" / "adb.exe")
S = "e4feca993701b30c"
REL = ROOT / "restore" / "release-1.1-mono-mira220-20261023"
SRC = REL / "camevision_boot_mono_wifi.pre-sd.img"
DST = REL / "camevision_boot_mono_wifi.img"


def adb(*args, t=120):
    r = subprocess.run([ADB, "-s", S, *args], capture_output=True, timeout=t)
    text = ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")
    if text.strip():
        print(text, end="" if text.endswith("\n") else "\n", flush=True)
    return r


print("patch", flush=True)
r = subprocess.run(
    [sys.executable, str(ROOT / "tools" / "patch_boot_am_sd.py"), str(SRC), str(DST)],
    cwd=str(ROOT),
)
if r.returncode != 0:
    raise SystemExit("patch failed")
(ROOT / "tools" / "camevision_boot_mono_wifi.img").write_bytes(DST.read_bytes())

print("push boot", flush=True)
r = adb("push", str(DST), "/userdata/camevision_boot_mono_wifi.img", t=180)
if r.returncode != 0:
    raise SystemExit("push failed")
print("push sd.sh", flush=True)
adb("push", str(ROOT / "tools" / "camevision-sd.sh"), "/userdata/camevision-sd.sh")
adb(
    "shell",
    "sed -i 's/\\r$//' /userdata/camevision-sd.sh; chmod 755 /userdata/camevision-sd.sh; "
    "dd if=/userdata/camevision_boot_mono_wifi.img of=/dev/mmcblk0p4 bs=65536 conv=fsync; "
    "sync; echo DD_OK",
    t=180,
)
print("reboot", flush=True)
adb("reboot", t=20)
print("wait ADB", flush=True)
time.sleep(8)
for i in range(40):
    r = subprocess.run([ADB, "devices"], capture_output=True, text=True)
    if S in r.stdout and "device" in r.stdout:
        print("UP", i, flush=True)
        break
    time.sleep(3)
else:
    raise SystemExit("no ADB after reboot")
time.sleep(4)
r = adb(
    "shell",
    "echo ---SD---; cat /sys/block/mmcblk1/size; "
    "cat /sys/class/mmc_host/mmc1/mmc1:*/type /sys/class/mmc_host/mmc1/mmc1:*/ocr; "
    "mkdir -p /mnt/sdcard; mount -t vfat /dev/mmcblk1p1 /mnt/sdcard; echo MOUNT:$?; "
    "df -h /mnt/sdcard; ls /mnt/sdcard; "
    "echo ---WLAN---; ip -4 addr show wlan0",
    t=30,
)
print("DONE", flush=True)
