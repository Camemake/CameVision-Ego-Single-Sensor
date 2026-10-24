#!/bin/sh
echo '=== dt mmc ==='
ls /proc/device-tree/mmc@21d60000
echo '=== dt props ==='
for f in /proc/device-tree/mmc@21d60000/*; do
	n=$(basename "$f")
	[ -d "$f" ] && continue
	echo -n "$n: "
	hexdump -C "$f" | head -2
done
echo '=== dmas ==='
ls /proc/device-tree/mmc@21d60000/dmas 2>/dev/null && hexdump -C /proc/device-tree/mmc@21d60000/dmas
ls /proc/device-tree/mmc@21d60000/dma-names 2>/dev/null && hexdump -C /proc/device-tree/mmc@21d60000/dma-names
echo '=== driver ==='
ls -l /sys/bus/platform/drivers | grep -iE 'dwmmc|sdhci|mmc'
echo DW
ls /sys/bus/platform/drivers/dwmmc_rockchip 2>/dev/null
echo '=== mmc tools ==='
which mmc 2>/dev/null
ls /usr/bin/mmc /usr/sbin/mmc 2>/dev/null
echo '=== dmesg fifo ==='
dmesg | grep -iE 'fifo|pio|idmac|21d60000|mmc1'
echo HOST
