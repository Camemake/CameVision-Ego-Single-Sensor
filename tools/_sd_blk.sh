#!/bin/sh
grep -E 'mmc_blk_probe|mmc_blk_alloc|set_capacity' /proc/kallsyms
echo size_ro=$(ls -l /sys/block/mmcblk1/size)
echo 30535680 > /sys/block/mmcblk1/size
echo after=$(cat /sys/block/mmcblk1/size)
echo BLK
