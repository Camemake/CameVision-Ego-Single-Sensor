#!/bin/sh
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind 2>/dev/null
sleep 1
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind
sleep 4
echo '=== dmesg ==='
dmesg | grep -E 'mmc1|mmcblk1' | tail -25
echo '=== card ==='
for d in /sys/class/mmc_host/mmc1/mmc1:*; do
	[ -d "$d" ] || continue
	echo "dev $d"
	for f in type name csd ocr scr; do
		[ -f "$d/$f" ] && echo " $f=$(cat $d/$f)"
	done
done
echo '=== parts ==='
cat /proc/partitions | grep mmcblk1
mkdir -p /mnt/sdcard
umount /mnt/sdcard 2>/dev/null
if [ -b /dev/mmcblk1p1 ]; then
	mount /dev/mmcblk1p1 /mnt/sdcard
elif [ -b /dev/mmcblk1 ]; then
	mount /dev/mmcblk1 /mnt/sdcard
fi
df -h | grep -E 'mmcblk1|sdcard'
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo REBIND
