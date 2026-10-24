#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "G=/sys/kernel/config/usb_gadget/rockchip; "
        "LUN=$G/functions/mass_storage.0/lun.0/file; "
        "kill $(ps | awk '/camevision-uvc-bridge.py/ && !/awk/ {print $1}') 2>/dev/null; "
        "echo none > $G/UDC; echo > $G/UDC; sleep 1; "
        "printf '' > $LUN; echo LUNCLR; cat $LUN; echo x; "
        "python3 /userdata/_fat_scan_board.py | tail -15; "
        "echo /dev/mmcblk1p1 > $LUN; "
        "echo 0 > $G/bDeviceClass; echo 0 > $G/bDeviceSubClass; echo 0 > $G/bDeviceProtocol; "
        "echo 21500000.usb > $G/UDC; sleep 1; "
        "echo LUN; cat $LUN; "
        "echo UDC; cat $G/UDC; cat /sys/class/udc/21500000.usb/state; "
        "setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 & "
        "setsid /bin/sh /userdata/camevision-usb-sd.sh </dev/null >>/userdata/cv-usb-sd.log 2>&1 & "
        "sleep 1; "
        "ps | grep -E 'uvc-bridge|usb-sd|single_live|camevision_agent|bluetoothd' | grep -v grep; "
        "ip -4 addr show wlan0 | grep inet",
        wait=12.0,
    )
)
