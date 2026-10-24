#!/usr/bin/env python3
import subprocess
import time

SERIAL = "e4feca993701b30c"


def sh(cmd, timeout=40):
    p = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        timeout=timeout,
    )
    text = ((p.stdout or b"") + (b"\n" + p.stderr if p.stderr else b"")).decode("utf-8", "replace")
    print(text)
    return text


print("=== net ===")
sh("ip -4 addr show wlan0; echo ---; cat /proc/skwsdio/bt_service 2>/dev/null; echo; echo ---; lsmod | grep -E 'skw|swt|wifi|bt'; echo ---; ls /userdata/swt6621-rt52/skwbt*; echo ---; ls /sys/class/bluetooth; echo ---; df -h /mnt/sdcard /mnt/sdcard/; echo ---; mount | grep mmcblk1")

print("=== insmod skwbt ===")
sh("printf start > /proc/skwsdio/bt_service; sleep 2; cat /proc/skwsdio/bt_service")
text = sh("insmod /userdata/swt6621-rt52/skwbt.ko; echo ins1=$?")
if "File exists" in text or "exists" in text:
    print("already loaded")
sh("lsmod | grep skwbt; ls /sys/class/bluetooth; dmesg | grep -iE 'skwbt|hci0|bt_service|sv6160|BT SERVICE' | tail -25")

for i in range(15):
    text = sh("hciconfig hci0 up; hciconfig hci0")
    if "BD Address" in text and "00:00:00:00:00:00" not in text:
        print("MAC_OK", i)
        break
    time.sleep(1)
else:
    print("still no mac, try skwbt_rt52")
    sh("rmmod skwbt; sleep 1; printf start > /proc/skwsdio/bt_service; sleep 2; insmod /userdata/swt6621-rt52/skwbt_rt52.ko; echo ins2=$?; sleep 2; hciconfig hci0 up; hciconfig hci0")

sh("hciconfig hci0 class 0x000620; hciconfig hci0 piscan; hciconfig hci0")
print("=== agent ===")
sh("ps | grep '[c]amevision_agent.py'; wget -q -O - http://127.0.0.1:8090/v1/status; echo; python3 -c 'import camevision_dbus,camevision_ble; print(\"imports_ok\")'")
print("BLE2_DONE")
