#!/bin/sh
# Only override mmc_blk_probe disk size. Do not change SDSC/SDHC addressing.
P=0x407b0300
echo before $(devmem $P 32) $(devmem $((P+4)) 32)
devmem $P 32 0xD29E0002
devmem $((P+4)) 32 0xF2A03A22
devmem $((P+8)) 32 0xD503201F
devmem $((P+12)) 32 0xD503201F
echo after $(devmem $P 32) $(devmem $((P+4)) 32)
umount /mnt/sdcard 2>/dev/null
echo 1 > /sys/class/mmc_host/mmc1/force_rescan
sleep 5
echo type=$(cat /sys/class/mmc_host/mmc1/mmc1:*/type)
cat /proc/partitions | grep mmcblk1
dmesg | grep -E 'mmcblk1:' | tail -6
echo SZ
