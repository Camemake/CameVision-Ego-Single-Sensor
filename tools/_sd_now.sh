#!/bin/sh
echo '=== dmesg sd ==='
dmesg | grep -iE 'mmc1|mmcblk1|sdmmc|sdhci|no card|vmmc|vqmmc|cd-gpios|error' | tail -40
echo '=== mmc hosts ==='
ls -d /sys/class/mmc_host/mmc* 2>/dev/null
for h in /sys/class/mmc_host/mmc*; do
	echo "-- $h"
	ls "$h" 2>/dev/null
	cat "$h/"*/type 2>/dev/null
	cat "$h/"*/name 2>/dev/null
done
echo '=== block ==='
cat /proc/partitions
ls -l /dev/mmcblk* 2>/dev/null
echo '=== mounts ==='
mount | grep -iE 'mmc|sd'
df -h
echo '=== fdt sd ==='
find /proc/device-tree -iname '*sd*' -o -iname '*mmc*' 2>/dev/null | head -40
echo NOW
