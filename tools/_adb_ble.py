#!/usr/bin/env python3
"""Finish BLE bring-up over adb. No PowerShell interpolation."""
import subprocess
import time

SERIAL = "e4feca993701b30c"


def sh(cmd, timeout=60):
    p = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        timeout=timeout,
    )
    out = (p.stdout or b"") + (b"\n" + p.stderr if p.stderr else b"")
    text = out.decode("utf-8", "replace")
    print(text)
    return text


def push(local, remote):
    print("PUSH", local, remote)
    subprocess.check_call(["adb", "-s", SERIAL, "push", local, remote])


print("=== state ===")
sh("hciconfig hci0; echo ---PS---; ps | grep -E 'camevision|bluetooth|skwbt|_ble_up' | grep -v grep; echo ---LOG---; tail -20 /userdata/camevision-agent.log")

print("=== push ===")
for name in (
    "camevision_dbus.py",
    "camevision_ble.py",
    "camevision_agent.py",
    "camevision-ble.sh",
    "camevision-wifi.sh",
):
    push(name, "/userdata/" + name)

sh("sed -i 's/\\r$//' /userdata/camevision_dbus.py /userdata/camevision_ble.py /userdata/camevision_agent.py /userdata/camevision-ble.sh /userdata/camevision-wifi.sh; chmod 755 /userdata/camevision-ble.sh /userdata/camevision-wifi.sh")

print("=== stop extras ===")
sh(
    "kill $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}') 2>/dev/null; "
    "kill $(ps | grep '[b]luetoothctl' | awk '{print $1}') 2>/dev/null; "
    "kill $(ps | grep '[c]amevision_agent.py' | awk '{print $1}') 2>/dev/null; "
    "kill $(ps | grep '[_]_ble_up' | awk '{print $1}') 2>/dev/null; "
    "true"
)
time.sleep(1)

print("=== reload skwbt ===")
sh("rmmod skwbt 2>/dev/null; true")
time.sleep(1)
sh("if [ -e /proc/skwsdio/bt_service ]; then printf start > /proc/skwsdio/bt_service; fi; ls /userdata/swt6621-rt52/skwbt.ko")
time.sleep(2)
sh("insmod /userdata/swt6621-rt52/skwbt.ko 2>/dev/null; true")

for i in range(20):
    text = sh("hciconfig hci0 up 2>/dev/null; hciconfig hci0")
    if "BD Address" in text and "00:00:00:00:00:00" not in text:
        print("MAC_OK", i)
        break
    time.sleep(1)
else:
    print("MAC_FAIL")

sh("hciconfig hci0 class 0x000620; hciconfig hci0 piscan; hciconfig hci0")

print("=== start agent ===")
sh("export PYTHONPATH=/userdata:/userdata/pylib; setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & echo $! >/tmp/camevision-agent.pid; cat /tmp/camevision-agent.pid")
time.sleep(2)
sh("setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 & echo $! >/tmp/camevision-ble.pid; cat /tmp/camevision-ble.pid")
time.sleep(4)
print("=== final ===")
sh("hciconfig hci0; echo ---; wget -q -O - http://127.0.0.1:8090/v1/status; echo; echo ---LOG---; tail -20 /userdata/camevision-agent.log; echo ADB_BLE_DONE")
