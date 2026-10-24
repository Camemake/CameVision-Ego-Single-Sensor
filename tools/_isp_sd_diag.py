#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo AM; ls -l /userdata/camevision-am.on /userdata/libsingle_color.so "
        "/userdata/libego_stereo.so /tmp/camevision-live.jpg /tmp/camevision-uvc.jpg "
        "/tmp/camevision-uvc-ctl.json 2>&1; "
        "echo CTL; cat /tmp/camevision-uvc-ctl.json; "
        "echo LIVE; ls -l /tmp/camevision-live.jpg /tmp/camevision-uvc.jpg; "
        "python3 -c \"import os\n"
        "for p in ('/tmp/camevision-live.jpg','/tmp/camevision-uvc.jpg'):\n"
        "    try:\n"
        "        d=open(p,'rb').read(16)\n"
        "        print(p, os.path.getsize(p), d[:2], list(d[:8]))\n"
        "    except Exception as e:\n"
        "        print(p, e)\n"
        "\"; "
        "echo LOG; tail -40 /userdata/single-live.log; "
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo MNT; grep sdcard /proc/mounts || echo none; "
        "echo FDISK; fdisk -l /dev/mmcblk1 2>/dev/null | head -20; "
        "echo PS; ps | grep -E 'single_live|uvc-bridge|usb-sd|camevision_agent' | grep -v grep",
        wait=10.0,
    )
)
