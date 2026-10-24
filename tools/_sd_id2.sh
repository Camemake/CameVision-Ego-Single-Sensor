#!/bin/sh
echo SERIAL=$(cat /proc/device-tree/serial-number | tr -d '\000')
echo '=== card ==='
for d in /sys/class/mmc_host/mmc1/mmc1:*; do
	[ -d "$d" ] || continue
	echo "dev $d"
	for f in type name cid csd ocr rca scr date manfid oemid serial; do
		[ -f "$d/$f" ] && echo " $f=$(cat $d/$f)"
	done
done
echo '=== ios ==='
cat /sys/kernel/debug/mmc1/ios 2>/dev/null || echo no-ios
echo '=== caps ==='
cat /sys/kernel/debug/mmc1/caps 2>/dev/null
echo CAPS2
cat /sys/kernel/debug/mmc1/caps2 2>/dev/null
echo '=== parts ==='
cat /proc/partitions
echo '=== df ==='
df -h /mnt/sdcard 2>/dev/null
df -h | grep -E 'mmcblk1|sdcard'
echo '=== dt ==='
hexdump -C /proc/device-tree/mmc@21d60000/status
echo BUS
hexdump -C /proc/device-tree/mmc@21d60000/bus-width
echo FREQ
hexdump -C /proc/device-tree/mmc@21d60000/max-frequency
echo HS
ls /proc/device-tree/mmc@21d60000/cap-sd-highspeed && echo hs-yes
ls /proc/device-tree/mmc@21d60000/no-1-8-v && echo no18-yes
echo '=== dmesg ==='
dmesg | grep -E 'mmc1|21d60000|mmcblk1' | head -40
echo ID2
