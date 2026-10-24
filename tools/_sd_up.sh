#!/bin/sh
echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/type 2>/dev/null)
echo OCR=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/ocr 2>/dev/null)
echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)
sh /userdata/camevision-sd.sh 2>/dev/null || true
df -h /mnt/sdcard 2>/dev/null
ip addr show wlan0 | grep inet
echo UP
