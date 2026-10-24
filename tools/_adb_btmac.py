#!/usr/bin/env python3
import subprocess
import time

SERIAL = "e4feca993701b30c"
NV = r"C:\Users\stefa\Desktop\Cursor packages\CameVision Single\restore\release-1.1-mono-mira220-20261023\overlay\swt6621_fw\sv6160lite.nvbin"


def sh(cmd, timeout=30):
    print(">>", cmd)
    p = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        timeout=timeout,
    )
    text = ((p.stdout or b"") + (b"\n" + p.stderr if p.stderr else b"")).decode("utf-8", "replace")
    print(text)
    return text


print("=== push 48-byte NV ===")
subprocess.check_call(["adb", "-s", SERIAL, "push", NV, "/userdata/swt6621_fw/sv6160lite.nvbin"])
sh("cp -f /userdata/swt6621_fw/sv6160lite.nvbin /lib/firmware/sv6160lite.nvbin 2>/dev/null; wc -c /userdata/swt6621_fw/sv6160lite.nvbin /lib/firmware/sv6160lite.nvbin")

print("=== reload skwbt only ===")
sh("rmmod skwbt; echo rm=$?")
time.sleep(1)
sh("printf start > /proc/skwsdio/bt_service; sleep 2; cat /proc/skwsdio/bt_service")
sh("insmod /userdata/swt6621-rt52/skwbt.ko; echo ins=$?")
time.sleep(1)

mac_ok = False
for i in range(25):
    text = sh("hciconfig hci0 up; hciconfig hci0")
    if "BD Address" in text and "00:00:00:00:00:00" not in text:
        print("MAC_OK", i)
        mac_ok = True
        break
    time.sleep(1)
if not mac_ok:
    print("MAC_FAIL")
    sh("dmesg | grep -iE 'skwbt|hci0|sv6160|nvbin|BT' | tail -30")

sh("hciconfig hci0 class 0x000620; hciconfig hci0 piscan; hciconfig hci0")

print("=== agent ===")
sh("kill $(ps | grep '[c]amevision_agent.py' | awk '{print $1}') 2>/dev/null; true")
time.sleep(1)
sh(
    "export PYTHONPATH=/userdata:/userdata/pylib; "
    "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
    "echo $! >/tmp/camevision-agent.pid"
)
time.sleep(2)
if "camevision-ble.sh" not in sh("ps | grep '[c]amevision-ble.sh'"):
    sh("setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 & echo $! >/tmp/camevision-ble.pid")
time.sleep(3)
sh("wget -q -O - http://127.0.0.1:8090/v1/status; echo")
sh("tail -20 /userdata/camevision-agent.log")
print("BTMAC_DONE")
