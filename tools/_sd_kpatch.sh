#!/bin/sh
echo '=== iomem ==='
grep -iE 'Kernel code|Kernel data' /proc/iomem
echo '=== mem ==='
ls -l /dev/mem /dev/kmem 2>/dev/null
which devmem
echo '=== modules ==='
ls /lib/modules 2>/dev/null | head
ls /sys/module | grep -i mmc
echo '=== kcore ==='
ls -l /proc/kcore
echo KP
