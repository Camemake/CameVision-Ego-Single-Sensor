#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "kill $(ps | grep '[c]amevision_agent.py' | awk '{print $1}') 2>/dev/null; sleep 1; "
        "umount /mnt/sdcard; "
        "busybox mkfs.vfat -v -n CAMEVISION /dev/mmcblk1p1 15267840; "
        "mkdir -p /mnt/sdcard; "
        "mount -t vfat -o utf8,flush /dev/mmcblk1p1 /mnt/sdcard; "
        "df -h /mnt/sdcard; "
        "echo ok > /mnt/sdcard/camevision.txt; "
        "ls -l /mnt/sdcard/camevision.txt; "
        "hciconfig hci0 up; hciconfig hci0; "
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; sleep 2; "
        "wget -q -O - http://127.0.0.1:8090/v1/status; echo; "
        "echo FAT16_DONE",
        wait=25,
    )
)
