#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "cd /userdata; "
        "wget -q -O camevision_agent.py http://192.168.1.44:18767/camevision_agent.py; "
        "wget -q -O camevision_dbus.py http://192.168.1.44:18767/camevision_dbus.py; "
        "wget -q -O camevision_ble.py http://192.168.1.44:18767/camevision_ble.py; "
        "wget -q -O camevision-ble.sh http://192.168.1.44:18767/camevision-ble.sh; "
        "wget -q -O camevision-wifi.sh http://192.168.1.44:18767/camevision-wifi.sh; "
        "mkdir -p /userdata/swt6621_fw; "
        "wget -q -O /userdata/swt6621_fw/sv6160lite.nvbin http://192.168.1.44:18767/sv6160lite.nvbin; "
        "wget -q -O /userdata/swt6621_fw/sv6160.nvbin http://192.168.1.44:18767/sv6160.nvbin; "
        "cp -f /userdata/swt6621_fw/sv6160lite.nvbin /userdata/swt6621_fw/sv6160lite.nvbin.ok; "
        "cp -f /userdata/swt6621_fw/sv6160.nvbin /userdata/swt6621_fw/sv6160.nvbin.ok; "
        "printf /userdata/swt6621_fw > /sys/module/firmware_class/parameters/path; "
        "wc -c /userdata/swt6621_fw/sv6160lite.nvbin /userdata/swt6621_fw/sv6160.nvbin camevision_dbus.py camevision_agent.py; "
        "echo PUSH_OK",
        wait=12,
    )
)

print(
    run(
        "for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do kill $p; done; "
        "for p in $(ps | grep '[b]luetoothctl' | awk '{print $1}'); do kill $p; done; "
        "rmmod skwbt; sleep 1; "
        "printf start > /proc/skwsdio/bt_service; sleep 3; "
        "cat /proc/skwsdio/bt_service; echo; "
        "insmod /userdata/swt6621-rt52/skwbt.ko; sleep 4; "
        "hciconfig hci0 up; "
        "hciconfig hci0; "
        "echo RELOAD_OK",
        wait=16,
    )
)
