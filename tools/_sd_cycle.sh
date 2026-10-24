#!/bin/sh
umount /mnt/sdcard 2>/dev/null
R=/sys/class/regulator/regulator.13
echo before $(cat $R/name) $(cat $R/state) $(cat $R/microvolts)
if [ -f $R/enable ]; then
	echo 0 > $R/enable
	sleep 1
	echo 1 > $R/enable
	sleep 1
	echo after $(cat $R/state)
else
	echo no-enable
fi
echo 1 > /sys/class/mmc_host/mmc1/force_rescan
sleep 4
for d in /sys/class/mmc_host/mmc1/mmc1:*; do
	[ -d "$d" ] || continue
	echo type=$(cat $d/type) ocr=$(cat $d/ocr)
	echo csd=$(cat $d/csd)
done
cat /proc/partitions | grep mmcblk1
dmesg | grep -E 'mmc1:|mmcblk1' | tail -8
echo CYCLE
