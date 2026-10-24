#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "cd /userdata; "
        "wget -q -O camevision_dbus.py http://192.168.1.44:18767/camevision_dbus.py; "
        "wget -q -O camevision_ble.py http://192.168.1.44:18767/camevision_ble.py; "
        "wget -q -O camevision_agent.py http://192.168.1.44:18767/camevision_agent.py; "
        "wget -q -O camevision-ble.sh http://192.168.1.44:18767/camevision-ble.sh; "
        "mkdir -p /userdata/swt6621_fw; "
        "wget -q -O /userdata/swt6621_fw/sv6160lite.nvbin http://192.168.1.44:18767/sv6160lite.nvbin; "
        "wc -c camevision_dbus.py /userdata/swt6621_fw/sv6160lite.nvbin; "
        "printf /userdata/swt6621_fw > /sys/module/firmware_class/parameters/path; "
        "echo TN3A",
        wait=10,
    )
)

print(
    run(
        "rmmod skwbt; sleep 1; "
        "printf start > /proc/skwsdio/bt_service; sleep 3; "
        "insmod /userdata/swt6621-rt52/skwbt.ko; sleep 5; "
        "hciconfig hci0 up; hciconfig hci0; "
        "echo TN3B",
        wait=16,
    )
)
