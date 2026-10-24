#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo STR; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming; "
        "echo MJ; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/mjpeg/m; "
        "echo UN; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/uncompressed 2>/dev/null; "
        "echo HDR; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/header; "
        "echo LINK; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/streaming/header/h; "
        "echo CTL; cat /tmp/camevision-uvc-ctl.json",
        wait=5.0,
    )
)
