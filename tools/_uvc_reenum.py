#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "G=/sys/kernel/config/usb_gadget/rockchip; "
        "kill $(ps | awk '/camevision-uvc-bridge.py/ && !/awk/ {print $1}') 2>/dev/null; "
        "echo none > $G/UDC; echo > $G/UDC; sleep 1; "
        "echo 0 > $G/bDeviceClass; echo 0 > $G/bDeviceSubClass; echo 0 > $G/bDeviceProtocol; "
        "echo 21500000.usb > $G/UDC; sleep 1; "
        "echo CLASS; cat $G/bDeviceClass; cat $G/bDeviceSubClass; cat $G/bDeviceProtocol; "
        "echo UDC; cat $G/UDC; cat /sys/class/udc/21500000.usb/state; "
        "echo VID; ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux; "
        "echo F01; cat $G/functions/uvc.gs1/streaming/mjpeg/m/f01_1400_1600_60/wWidth; "
        "cat $G/functions/uvc.gs1/streaming/mjpeg/m/f01_1400_1600_60/wHeight; "
        "echo LUN; cat $G/functions/mass_storage.0/lun.0/file; "
        "setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 & "
        "sleep 1; tail -8 /userdata/cv-uvc-bridge.log; "
        "ps | grep uvc-bridge | grep -v grep; "
        "ip -4 addr show wlan0 | grep inet",
        wait=12.0,
    )
)
