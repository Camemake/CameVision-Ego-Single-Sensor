#!/bin/sh
umount /mnt/sdcard 2>/dev/null
PH=/sys/kernel/debug/clk/cclk_sdmmc0/clk_phase
for p in 0 45 90 135 180 225 270 315; do
	echo $p > "$PH"
	echo 1 > /sys/class/mmc_host/mmc1/force_rescan
	sleep 3
	t=$(cat /sys/class/mmc_host/mmc1/mmc1:*/type 2>/dev/null | tr -d '\n')
	o=$(cat /sys/class/mmc_host/mmc1/mmc1:*/ocr 2>/dev/null | tr -d '\n')
	sz=$(grep mmcblk1$ /proc/partitions | awk '{print $3}')
	echo "phase=$p clk=$(cat $PH) type=$t ocr=$o sz=$sz"
	echo "$sz" | grep -q 1952256 || { echo HIT; break; }
	echo "$t" | grep -q SDHC && { echo HIT; break; }
done
echo PHASE
