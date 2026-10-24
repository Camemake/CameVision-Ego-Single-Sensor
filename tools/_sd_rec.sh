#!/bin/sh
echo 1 > /sys/class/mmc_host/mmc1/force_rescan
sleep 3
mkdir -p /mnt/sdcard
mount /dev/mmcblk1p1 /mnt/sdcard 2>/dev/null || mount /dev/mmcblk1 /mnt/sdcard 2>/dev/null
echo type=$(cat /sys/class/mmc_host/mmc1/mmc1:*/type 2>/dev/null)
cat /proc/partitions | grep mmcblk1
echo '=== clk ==='
find /sys/kernel/debug/clk -iname '*mmc*' -o -iname '*sdmmc*' 2>/dev/null | head -40
echo '=== summary ==='
cat /sys/kernel/debug/clk/clk_summary 2>/dev/null | grep -iE 'mmc|sdmmc|21d6' | head -30
echo REC
