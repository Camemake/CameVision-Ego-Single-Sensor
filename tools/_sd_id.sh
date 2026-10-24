#!/bin/sh
echo '=== card ==='
for d in /sys/class/mmc_host/mmc1/mmc1:*; do
	[ -d "$d" ] || continue
	echo "dev $d"
	for f in type name cid csd ocr rca scr ssr date manfid oemid serial; do
		[ -f "$d/$f" ] && echo " $f=$(cat $d/$f)"
	done
done
echo '=== ios ==='
cat /sys/kernel/debug/mmc1/ios
echo '=== caps ==='
cat /sys/kernel/debug/mmc1/caps
echo CAPS2
cat /sys/kernel/debug/mmc1/caps2
echo '=== parts ==='
cat /proc/partitions
echo '=== dmesg ==='
dmesg | grep -E 'mmc1|21d60000' | head -25
echo ID
