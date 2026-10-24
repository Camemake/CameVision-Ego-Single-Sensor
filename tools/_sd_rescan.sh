#!/bin/sh
dmesg -C 2>/dev/null || true
echo 1 > /sys/class/mmc_host/mmc1/force_rescan
sleep 3
echo '=== dmesg ==='
dmesg | grep -E 'mmc1|mmcblk1' | tail -20
echo '=== type ==='
cat /sys/class/mmc_host/mmc1/mmc1:*/type 2>/dev/null
cat /sys/class/mmc_host/mmc1/mmc1:*/csd 2>/dev/null
cat /sys/class/mmc_host/mmc1/mmc1:*/ocr 2>/dev/null
cat /proc/partitions | grep mmcblk1
echo RESCAN
