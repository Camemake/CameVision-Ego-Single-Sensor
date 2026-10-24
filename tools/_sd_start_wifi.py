#!/usr/bin/env python3
import subprocess
import time

ADB = r"C:\Users\stefa\Desktop\Cursor packages\CameVision Single\host\adb.exe"
S = "e4feca993701b30c"


def sh(cmd, t=40):
    r = subprocess.run([ADB, "-s", S, "shell", cmd], capture_output=True, text=True, timeout=t)
    print((r.stdout or "") + (r.stderr or ""), end="", flush=True)
    return r


sh(
    "chmod 755 /userdata/camevision-wifi.sh /userdata/camevision-ble.sh "
    "/userdata/camevision-hw.sh /userdata/camevision-sd.sh "
    "/userdata/camevision-single.sh /userdata/S10mira220; "
    "sed -i 's/\\r$//' /userdata/camevision-wifi.sh /userdata/camevision-ble.sh "
    "/userdata/camevision-sd.sh; "
    "sh /userdata/camevision-hw.sh >/userdata/hw-boot.log 2>&1; "
    "setsid /bin/sh /userdata/camevision-wifi.sh </dev/null >/userdata/wifi-boot.log 2>&1 & "
    "setsid /bin/sh /userdata/camevision-ble.sh </dev/null >/userdata/ble-boot.log 2>&1 & "
    "echo STARTED"
)
for i in range(20):
    r = sh("ip -4 addr show wlan0 2>/dev/null | grep inet || true")
    if "inet " in (r.stdout or ""):
        print("WIFI_OK", i, flush=True)
        break
    time.sleep(3)
else:
    print("WIFI_WAIT", flush=True)
    sh("tail -30 /userdata/wifi-boot.log")
sh("df -h /mnt/sdcard; cat /userdata/sd-mount.log; hciconfig 2>/dev/null | head -6")
