#!/bin/sh
echo '=== start ==='
cat /sys/block/mmcblk1/mmcblk1p1/start
cat /sys/block/mmcblk1/mmcblk1p1/size
cat /sys/block/mmcblk1/size
echo '=== MBR ==='
dd if=/dev/mmcblk1 bs=512 count=1 2>/dev/null | hexdump -C
echo '=== sec32 ==='
dd if=/dev/mmcblk1 bs=512 skip=32 count=1 2>/dev/null | hexdump -C | head -8
echo '=== sec129 ==='
dd if=/dev/mmcblk1 bs=512 skip=129 count=1 2>/dev/null | hexdump -C | head -8
echo '=== p1 bpb ==='
dd if=/dev/mmcblk1p1 bs=512 count=1 2>/dev/null | hexdump -C | head -6
echo '=== dw ==='
grep dw_mci /proc/kallsyms | head -30
echo MBR
