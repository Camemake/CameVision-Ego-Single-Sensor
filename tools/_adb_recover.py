#!/usr/bin/env python3
import subprocess
import time

SERIAL = "e4feca993701b30c"


def sh(cmd, timeout=90):
    p = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        timeout=timeout,
    )
    text = ((p.stdout or b"") + (b"\n" + p.stderr if p.stderr else b"")).decode("utf-8", "replace")
    print(text)
    return text


print("=== uptime / sdio / fat ===")
sh(
    "cat /proc/uptime; echo ---; "
    "ls /sys/bus/sdio/devices; echo ---; "
    "lsmod; echo ---; "
    "hexdump -C /dev/mmcblk1p1 | head -2; echo ---; "
    "ls /userdata/swt6621-rt52; echo ---; "
    "tail -30 /userdata/wifi.log"
)

print("=== wifi.sh ===")
sh("sed -i 's/\\r$//' /userdata/camevision-wifi.sh /userdata/camevision-ble.sh; chmod 755 /userdata/camevision-wifi.sh /userdata/camevision-ble.sh")
sh("/bin/sh /userdata/camevision-wifi.sh", timeout=90)

print("=== after wifi ===")
sh(
    "ip -4 addr show wlan0; echo ---; "
    "cat /proc/skwsdio/bt_service 2>/dev/null; echo; echo ---; "
    "lsmod | grep -E 'skw|swt|wifi|bt'; echo ---; "
    "hciconfig hci0; echo ---; "
    "ls /sys/class/bluetooth"
)

print("=== fat16 if needed ===")
df = sh("df -h /mnt/sdcard")
if "1.9G" in df or "1.8G" in df:
    print("reapply 16G FAT label on p1 only")
    sh(
        "umount /mnt/sdcard; "
        "busybox mkfs.vfat -v -n CAMEVISION /dev/mmcblk1p1 15267840; "
        "mkdir -p /mnt/sdcard; "
        "mount -t vfat -o utf8,flush /dev/mmcblk1p1 /mnt/sdcard; "
        "df -h /mnt/sdcard; "
        "echo ok > /mnt/sdcard/camevision.txt; "
        "ls -l /mnt/sdcard/camevision.txt"
    )

print("=== agent restart ===")
sh(
    "kill $(ps | grep '[c]amevision_agent.py' | awk '{print $1}') 2>/dev/null; true"
)
time.sleep(1)
sh(
    "export PYTHONPATH=/userdata:/userdata/pylib; "
    "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
    "echo $! >/tmp/camevision-agent.pid; cat /tmp/camevision-agent.pid"
)
time.sleep(3)
if not sh("ps | grep '[c]amevision-ble.sh'"):
    sh(
        "setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 & "
        "echo $! >/tmp/camevision-ble.pid"
    )
time.sleep(2)
print("=== final ===")
sh(
    "hciconfig hci0; echo ---; "
    "wget -q -O - http://127.0.0.1:8090/v1/status; echo; echo ---; "
    "tail -25 /userdata/camevision-agent.log; echo RECOVER_DONE"
)
