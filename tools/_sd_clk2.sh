#!/bin/sh
echo '=== summary sd ==='
cat /sys/kernel/debug/clk/clk_summary | grep -iE 'sdmmc|sample|drv|mmc'
echo '=== dirs ==='
ls -d /sys/kernel/debug/clk/* | grep -iE 'sd|mmc|sample|drv'
echo CLK2
