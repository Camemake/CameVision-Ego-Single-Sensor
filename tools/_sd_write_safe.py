#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "kill $(ps | awk '/camevision-usb-sd.sh/ && !/awk/ {print $1}') 2>/dev/null; "
        "sleep 0.3; "
        "LUN=/sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "i=0; while [ $i -lt 8 ]; do printf '' > $LUN; got=$(cat $LUN); "
        "[ -z \"$got\" ] && break; sleep 0.5; i=$((i+1)); done; "
        "echo LUN1; cat $LUN; echo empty; "
        "sync; umount /mnt/sdcard 2>/dev/null; "
        "sleep 2; "
        "mkdir -p /mnt/sdcard; "
        "mount -t vfat -o utf8,flush /dev/mmcblk1p1 /mnt/sdcard || echo MOUNT_FAIL; "
        "echo MNT; grep sdcard /proc/mounts; "
        "mkdir -p /mnt/sdcard/camevision/sessions; "
        "echo CameVision > /mnt/sdcard/camevision.txt; "
        "sync; "
        "echo AFTER; ls -la /mnt/sdcard; "
        "umount /mnt/sdcard || echo UMOUNT_FAIL; "
        "sync; "
        "echo SCAN; python3 /userdata/_fat_scan_board.py",
        wait=14.0,
    )
)
