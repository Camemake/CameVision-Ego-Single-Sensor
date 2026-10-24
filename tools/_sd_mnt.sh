#!/bin/sh
/userdata/camevision-sd.sh
sleep 1
mount | grep sdcard
df -h /mnt/sdcard
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo MNT
