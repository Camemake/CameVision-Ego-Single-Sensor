#!/bin/sh
# Restore mmc_send_if_cond (must still send CMD8), NOP the error check
# in mmc_sd_get_cid so ACMD41 always includes HCS.
IF=0x407a89f8
CID=0x407a756c
echo '=== restore if_cond ==='
devmem $IF 32 0xA9BF7BFD
devmem $((IF+4)) 32 0xD2800003
devmem $((IF+8)) 32 0x52800002
devmem $((IF+12)) 32 0x910003FD
echo '=== nop get_cid cbnz ==='
devmem $CID 32
devmem $CID 32 0xD503201F
devmem $CID 32
echo 1 > /sys/class/mmc_host/mmc1/force_rescan
sleep 5
echo '=== card ==='
for d in /sys/class/mmc_host/mmc1/mmc1:*; do
	[ -d "$d" ] || continue
	echo "dev $d"
	for f in type name csd ocr scr; do
		[ -f "$d/$f" ] && echo " $f=$(cat $d/$f)"
	done
done
cat /proc/partitions | grep mmcblk1
dmesg | grep -E 'mmc1:|mmcblk1' | tail -12
echo HCSNOW
