#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "cd /userdata; "
        "wget -q -O _lock_uvc_safe.sh http://192.168.1.44:18770/_lock_uvc_safe.sh; "
        "sed -i 's/\\r$//' _lock_uvc_safe.sh; chmod 755 _lock_uvc_safe.sh; "
        "grep -n DeviceClass _lock_uvc_safe.sh; "
        "echo LIVECLASS; "
        "cat /sys/kernel/config/usb_gadget/rockchip/bDeviceClass; "
        "cat /sys/kernel/config/usb_gadget/rockchip/bDeviceSubClass; "
        "cat /sys/kernel/config/usb_gadget/rockchip/bDeviceProtocol; "
        "echo BRIDGE; tail -15 /userdata/cv-uvc-bridge.log; "
        "echo PS; ps | grep -E 'uvc-bridge|single_live|usb-sd|camevision_agent|bluetoothd' | grep -v grep",
        wait=8.0,
    )
)
