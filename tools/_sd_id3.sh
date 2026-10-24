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
echo '=== parts ==='
cat /proc/partitions
echo '=== df ==='
df -h | grep -E 'mmcblk1|sdcard'
echo '=== fifo ==='
ls /proc/device-tree/mmc@21d60000/fifo-mode && echo fifo-yes
echo '=== dmesg ==='
dmesg | grep -E 'mmc1|21d60000|mmcblk1' | tail -30
echo '=== agent ==='
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo ID3
