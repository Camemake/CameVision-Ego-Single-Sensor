#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "python3 /userdata/_fat_scan_board.py; "
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo MNT; grep sdcard /proc/mounts || echo none",
        wait=5.0,
    )
)
