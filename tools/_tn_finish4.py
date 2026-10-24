#!/usr/bin/env python3
from cv_tn import run

print("=== now ===")
print(run("hciconfig hci0; ip -4 addr show wlan0 | head -3; wget -q -O - http://127.0.0.1:8090/v1/status; echo; echo TN4A", wait=5))

print("=== fat16 ===")
print(
    run(
        "kill $(ps | grep '[c]amevision_agent.py' | awk '{print $1}') 2>/dev/null; sleep 1; "
        "umount /mnt/sdcard; "
        "busybox mkfs.vfat -v -n CAMEVISION /dev/mmcblk1p1 15267840; "
        "mkdir -p /mnt/sdcard; "
        "mount -t vfat -o utf8,flush /dev/mmcblk1p1 /mnt/sdcard; "
        "df -h /mnt/sdcard; "
        "echo ok > /mnt/sdcard/camevision.txt; "
        "ls -l /mnt/sdcard/camevision.txt; "
        "echo TN4B",
        wait=20,
    )
)

print("=== agent ===")
print(
    run(
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; sleep 2; "
        "if ! ps | grep '[c]amevision-ble.sh' | grep -v grep; then "
        "setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 & "
        "echo $! >/tmp/camevision-ble.pid; fi; "
        "wget -q -O - http://127.0.0.1:8090/v1/status; echo; "
        "tail -12 /userdata/camevision-agent.log; "
        "hciconfig hci0; echo TN4C",
        wait=8,
    )
)
