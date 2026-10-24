#!/bin/sh
echo CID=$(devmem 0x407a756c 32)
echo IF=$(devmem 0x407a89f8 32)
echo '=== sys ==='
for d in /sys/class/mmc_host/mmc1/mmc1:*; do
	[ -d "$d" ] || continue
	echo $d
	cat $d/type
	cat $d/ocr
	cat $d/csd
	cat $d/scr
done
echo CHK
