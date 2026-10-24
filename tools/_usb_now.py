#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo UDC; cat /sys/class/udc/21500000.usb/state 2>/dev/null; "
        "cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null; "
        "cat /sys/kernel/config/usb_gadget/rockchip/idProduct 2>/dev/null; "
        "echo ---CFG; ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1 2>/dev/null; "
        "echo ---FN; ls /sys/kernel/config/usb_gadget/rockchip/functions 2>/dev/null; "
        "echo ---VID; ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux 2>/dev/null; "
        "echo ---IV; "
        "U=/sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1; "
        "ls $U/streaming/mjpeg/m 2>/dev/null; "
        "for D in $U/streaming/mjpeg/m/*; do "
        "[ -d \"$D\" ] || continue; "
        "echo FRAME $D w=$(cat $D/wWidth) h=$(cat $D/wHeight) def=$(cat $D/dwDefaultFrameInterval); "
        "echo -n IV=; tr '\\n' ',' < $D/dwFrameInterval; echo; "
        "done; "
        "echo ---BM; "
        "od -An -tx1 $U/control/terminal/camera/default/bmControls 2>/dev/null; "
        "od -An -tx1 $U/control/processing/default/bmControls 2>/dev/null; "
        "echo ---PS; ps | grep -E 'uvc-bridge|single_live|rkaiq|S50|adbd' | grep -v grep; "
        "echo ---S50; head -5 /etc/init.d/S50usbdevice; "
        "echo ---SD; cat /proc/mounts | grep vfat; ls -l /dev/mmcblk1*",
        wait=8.0,
    )
)
