#!/usr/bin/env python3
import subprocess
import time

SERIAL = "e4feca993701b30c"


def sh(cmd: str, timeout: int = 25) -> str:
    r = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return (r.stdout or "") + (r.stderr or "")


print("=== uptime / patches ===")
print(sh("uptime; echo ---; head -2 /usr/bin/usbdevice; echo ---; ls /lib/udev/rules.d/61-usbdevice.rules*; echo ---; grep -n CV_NO_RESTART /etc/init.d/S50usbdevice; echo ---; cat /tmp/.usb_config; echo ---; cat /sys/kernel/config/usb_gadget/rockchip/idProduct; cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product; echo ---; ip -4 addr show wlan0 | grep inet; echo ---; ps | grep -E 'single_live|telnetd|adbd|usbdevice' | grep -v grep"))
print("=== dmesg usb ===")
print(sh("dmesg | tail -40"))
