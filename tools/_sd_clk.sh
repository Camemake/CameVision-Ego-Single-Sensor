#!/bin/sh
echo '=== cclk_sdmmc0 ==='
ls /sys/kernel/debug/clk/cclk_sdmmc0
echo '=== files ==='
for f in /sys/kernel/debug/clk/cclk_sdmmc0/*; do
	[ -f "$f" ] || continue
	echo -n "$(basename $f)="
	cat "$f" 2>/dev/null | tr '\n' ' '
	echo
done
echo '=== all sdmmc ==='
ls -d /sys/kernel/debug/clk/*sdmmc* /sys/kernel/debug/clk/*sample* /sys/kernel/debug/clk/*drv* 2>/dev/null
echo CLK
