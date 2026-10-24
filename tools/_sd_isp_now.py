#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo ---LUNINFO; ls -l /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0; "
        "for f in file ro removable cdrom nofua inquiry_string; do "
        "  echo -n $f=; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/$f 2>/dev/null; echo; "
        "done; "
        "echo ---BLK; ls -l /dev/mmcblk1 /dev/mmcblk1p1; cat /sys/block/mmcblk1/size; cat /sys/block/mmcblk1/mmcblk1p1/size 2>/dev/null; "
        "echo ---MNT; grep -E 'mmc|sdcard|vfat' /proc/mounts; "
        "echo ---FDISK; fdisk -l /dev/mmcblk1 2>/dev/null | head -20; "
        "echo ---HEX; dd if=/dev/mmcblk1p1 bs=512 count=1 2>/dev/null | od -An -tx1 | head -4; "
        "echo ---LABEL; dd if=/dev/mmcblk1p1 bs=1 skip=43 count=11 2>/dev/null; echo; "
        "echo ---REC; ls -l /tmp/camevision-record.on /tmp/camevision-live.jpg /tmp/camevision-uvc-ctl.json 2>/dev/null; "
        "echo ---CTL; cat /tmp/camevision-uvc-ctl.json 2>/dev/null; "
        "echo ---LIVE; python3 -c 'import os; p=\"/tmp/camevision-live.jpg\"; print(os.path.getsize(p) if os.path.isfile(p) else 0)'; "
        "echo ---AIQ; ps | grep -E 'rkaiq|single_live|S10mira' | grep -v grep; "
        "echo ---SDLOG; tail -15 /userdata/cv-usb-sd.log",
        wait=8.0,
    )
)
