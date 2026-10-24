#!/bin/sh
# Force CSD v1 decode to 16 GB + block addressing (Windows D: 30535680 sectors).
P=0x407a7710
devmem $P 32 0x529E0004
devmem $((P+4)) 32 0x72A03A24
devmem $((P+8)) 32 0xB9002444
devmem $((P+12)) 32 0xB9435E64
devmem $((P+16)) 32 0x321E0084
devmem $((P+20)) 32 0xB9035E64
devmem $((P+24)) 32 0x52800124
devmem $((P+28)) 32 0xB9001C44
echo patched
umount /mnt/sdcard 2>/dev/null
echo 1 > /sys/class/mmc_host/mmc1/force_rescan
sleep 4
echo '=== card ==='
cat /sys/class/mmc_host/mmc1/mmc1:*/type
cat /sys/class/mmc_host/mmc1/mmc1:*/ocr
cat /proc/partitions | grep mmcblk1
dmesg | grep -E 'mmc1:|mmcblk1' | tail -10
echo CAP
