#!/bin/sh
echo '=== mmc1 ==='
ls /sys/class/mmc_host/mmc1 2>/dev/null
for d in /sys/class/mmc_host/mmc1/mmc1:*; do
	[ -d "$d" ] || continue
	echo "dev $d"
	for f in type name cid csd ocr rca date fwrev hwrev manfid oemid serial preferred_erase_size; do
		[ -f "$d/$f" ] && echo " $f=$(cat $d/$f)"
	done
done
echo '=== ios ==='
cat /sys/kernel/debug/mmc1/ios 2>/dev/null
echo '=== parts ==='
cat /proc/partitions
echo '=== mounts ==='
mount | grep -E 'mmcblk1|sdcard'
df -h /mnt/sdcard /dev/mmcblk1p1 2>/dev/null
echo '=== dmesg card ==='
dmesg | grep -E 'mmc1:|mmcblk1' | head -20
echo '=== live ==='
ps | grep -E 'single_live|ffmpeg|camevision_agent' | grep -v grep
ls -l /tmp/camevision-live.jpg /tmp/camevision-aim.jpg /tmp/camevision-aim.on /tmp/camevision-record.on /tmp/camevision-record.geom /dev/video1 2>/dev/null
echo '=== live log ==='
tail -20 /userdata/single-live.log 2>/dev/null
echo '=== agent tail ==='
tail -30 /userdata/camevision-agent.log
echo '=== video log ==='
tail -15 /userdata/camevision-video.log 2>/dev/null
echo NOW
