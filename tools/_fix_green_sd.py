#!/usr/bin/env python3
"""Restore official AM color and put session files on the FAT Windows mounts."""
import cv_tn

print(
    cv_tn.run(
        "cd /userdata; "
        "wget -q -O single_live.py http://192.168.1.44:18770/single_live.py; "
        "wget -q -O camevision-uvc-bridge.py http://192.168.1.44:18770/camevision-uvc-bridge.py; "
        "wget -q -O camevision-usb-sd.sh http://192.168.1.44:18770/camevision-usb-sd.sh; "
        "wget -q -O _fat_scan_board.py http://192.168.1.44:18770/_fat_scan_board.py; "
        "sed -i 's/\\r$//' single_live.py camevision-uvc-bridge.py camevision-usb-sd.sh _fat_scan_board.py; "
        "chmod 755 camevision-usb-sd.sh; "
        "echo FAT; python3 /userdata/_fat_scan_board.py; "
        "kill $(ps | awk '/camevision-usb-sd.sh/ && !/awk/ {print $1}') 2>/dev/null; "
        "kill $(ps | awk '/camevision-uvc-bridge.py/ && !/awk/ {print $1}') 2>/dev/null; "
        "kill $(ps | awk '/single_live.py/ && !/awk/ {print $1}') 2>/dev/null; "
        "sleep 1; "
        "printf '' > /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "sync; umount /mnt/sdcard 2>/dev/null; "
        "mkdir -p /mnt/sdcard; "
        "mount -t vfat -o utf8,flush /dev/mmcblk1p1 /mnt/sdcard; "
        "echo MNT; grep sdcard /proc/mounts || echo none; "
        "echo BEFORE; ls -la /mnt/sdcard; "
        "mkdir -p /mnt/sdcard/camevision/sessions; "
        "echo CameVision > /mnt/sdcard/camevision.txt; "
        "sync; "
        "echo AFTER; ls -la /mnt/sdcard; ls -la /mnt/sdcard/camevision; "
        "sync; umount /mnt/sdcard; "
        "echo /dev/mmcblk1p1 > /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "rm -f /tmp/camevision-uvc-ctl.json; "
        "setsid /bin/sh /userdata/camevision-usb-sd.sh </dev/null >>/userdata/cv-usb-sd.log 2>&1 & "
        "setsid /usr/bin/python3 /userdata/single_live.py </dev/null >>/userdata/single-live.log 2>&1 & "
        "setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 & "
        "sleep 2; "
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo CTL; cat /tmp/camevision-uvc-ctl.json; "
        "echo PS; ps | grep -E 'single_live|uvc-bridge|usb-sd|camevision_agent|bluetoothd' | grep -v grep; "
        "ip -4 addr show wlan0 | grep inet",
        wait=16.0,
    )
)
