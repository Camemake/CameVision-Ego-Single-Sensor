#!/bin/sh
echo '=== mmc2 ==='
ls -la /sys/bus/mmc/devices/mmc2:0001 2>/dev/null
cat /sys/bus/mmc/devices/mmc2:0001/type 2>/dev/null
cat /sys/bus/mmc/devices/mmc2:0001/name 2>/dev/null
cat /sys/bus/mmc/devices/mmc2:0001/cid 2>/dev/null
cat /sys/bus/mmc/devices/mmc2:0001/csd 2>/dev/null
cat /sys/bus/mmc/devices/mmc2:0001/date 2>/dev/null
cat /sys/bus/mmc/devices/mmc2:0001/serial 2>/dev/null
cat /sys/bus/mmc/devices/mmc2:0001/oemid 2>/dev/null
ls /sys/bus/mmc/devices/mmc2:0001/block 2>/dev/null
echo '=== mmc0 ==='
cat /sys/bus/mmc/devices/mmc0:0001/type 2>/dev/null
cat /sys/bus/mmc/devices/mmc0:0001/name 2>/dev/null
echo '=== removable ==='
for d in /sys/block/mmcblk*; do
	echo "$d rem=$(cat $d/removable 2>/dev/null) size=$(cat $d/size 2>/dev/null)"
done
echo '=== dmesg mmc ==='
dmesg | grep -iE 'mmc2|mmc1|sdcard|sdhci|no card' | tail -20
echo MMC2
