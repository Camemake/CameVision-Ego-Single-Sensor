#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo FRAMES; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/mjpeg/m; "
        "echo F01; cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/mjpeg/m/f01_1400_1600_60/wWidth; "
        "cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/mjpeg/m/f01_1400_1600_60/wHeight; "
        "cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/mjpeg/m/f01_1400_1600_60/dwFrameInterval; "
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo CFG; ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1; "
        "echo MNT; grep sdcard /proc/mounts; "
        "echo SDLOG; tail -10 /userdata/cv-usb-sd.log; "
        "echo PS; ps | grep -E 'uvc-bridge|usb-sd|single_live|camevision_agent|bluetoothd' | grep -v grep; "
        "echo WLAN; ip -4 addr show wlan0 | grep inet",
        wait=6.0,
    )
)
