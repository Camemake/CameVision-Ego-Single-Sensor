#!/usr/bin/env python3
import subprocess
import time

SERIAL = "e4feca993701b30c"


def sh(cmd, timeout=25):
    print(">>", cmd)
    p = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        timeout=timeout,
    )
    text = ((p.stdout or b"") + (b"\n" + p.stderr if p.stderr else b"")).decode("utf-8", "replace")
    print(text)
    return text


print("=== ping ===")
sh("echo ok; cat /proc/uptime")
print("=== sdio ===")
sh("ls /sys/bus/sdio/devices")
print("=== lsmod ===")
sh("lsmod")
print("=== wifi.sh ===")
sh("/bin/sh /userdata/camevision-wifi.sh", timeout=80)
print("=== wlan ===")
sh("ip -4 addr show wlan0")
print("=== bt ===")
sh("cat /proc/skwsdio/bt_service 2>/dev/null; echo; hciconfig hci0")
print("=== agent ===")
sh("wget -q -O - http://127.0.0.1:8090/v1/status; echo")
print("REC2_DONE")
