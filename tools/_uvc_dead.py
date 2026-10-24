#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo UDC; cat /sys/class/udc/21500000.usb/state; "
        "cat /sys/kernel/config/usb_gadget/rockchip/UDC; "
        "cat /sys/kernel/config/usb_gadget/rockchip/idProduct; "
        "echo CFG; ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1; "
        "echo F1; readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1; "
        "echo F2; readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2; "
        "echo VID; ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux 2>/dev/null; "
        "ls /dev/video* 2>/dev/null; "
        "echo F01; cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/mjpeg/m/f01_1400_1600_60/wWidth 2>/dev/null; "
        "cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/mjpeg/m/f01_1400_1600_60/wHeight 2>/dev/null; "
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo PS; ps | grep -E 'uvc-bridge|single_live|usb-sd|camevision_agent|bluetoothd' | grep -v grep; "
        "echo BRIDGE; tail -25 /userdata/cv-uvc-bridge.log; "
        "echo LOCK; tail -20 /userdata/cv-rk-uvc.log; "
        "echo WLAN; ip -4 addr show wlan0 | grep inet",
        wait=8.0,
    )
)
