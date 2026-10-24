#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo MOUNTPT; ls -la /mnt/sdcard 2>&1; echo SESS; "
        "ls -la /mnt/sdcard/camevision/sessions 2>&1; "
        "find /mnt/sdcard /userdata /tmp /oem -maxdepth 4 -type d -name sessions 2>/dev/null; "
        "find /mnt/sdcard /userdata /tmp -name 'video.mp4' -o -name 'camevision.txt' 2>/dev/null; "
        "echo MOUNTS; cat /proc/mounts | grep -E 'sd|mmc|vfat'; "
        "echo JPG; ls -l /tmp/camevision-live.jpg /tmp/camevision-uvc.jpg; "
        "python3 -c \""
        "d=open('/tmp/camevision-live.jpg','rb').read();"
        "print('jpg',len(d),d[:4],d[-2:]);"
        "\"",
        wait=8.0,
    )
)
