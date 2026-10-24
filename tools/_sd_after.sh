#!/bin/sh
echo SERIAL=$(cat /proc/device-tree/serial-number | tr -d '\000')
echo COMPAT=$(tr '\000' ' ' < /proc/device-tree/mmc@21d60000/compatible)
echo PHASE=$(hexdump -v -e '/4 "%u\n"' /proc/device-tree/mmc@21d60000/rockchip,default-sample-phase)
p=$(ls -d /sys/class/mmc_host/mmc1/mmc1:* 2>/dev/null | head -1)
echo P=$p
echo TYPE=$(cat $p/type 2>/dev/null)
echo NAME=$(cat $p/name 2>/dev/null)
echo OCR=$(cat $p/ocr 2>/dev/null)
echo CSD=$(cat $p/csd 2>/dev/null)
echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)
dmesg | grep -E 'mmc1|21d60000' | head -20
sh /userdata/camevision-sd.sh 2>/dev/null || true
df -h /mnt/sdcard 2>/dev/null
echo AFTER
