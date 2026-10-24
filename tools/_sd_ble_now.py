#!/usr/bin/env python3
import os
import time

print("bt_svc", open("/proc/skwsdio/bt_service").read().strip() if os.path.exists("/proc/skwsdio/bt_service") else "none")
print("hci_sys", os.path.exists("/sys/class/bluetooth/hci0"))
if os.path.exists("/proc/skwsdio/bt_service"):
    open("/proc/skwsdio/bt_service", "w").write("start\n")
    time.sleep(2)
    print("bt_svc2", open("/proc/skwsdio/bt_service").read().strip())
os.system("hciconfig hci0 2>/dev/null | head -8")
os.system("ps | grep -E 'camevision_agent|camevision_ble|camevision-ble|bluetoothd' | grep -v grep")
os.system("tail -20 /userdata/camevision-agent.log 2>/dev/null")
os.system("tail -15 /userdata/wifi-boot.log 2>/dev/null")
os.system("tail -15 /userdata/ble-adv.log 2>/dev/null")
