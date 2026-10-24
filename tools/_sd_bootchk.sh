#!/bin/sh
echo SERIAL=$(cat /proc/device-tree/serial-number | tr -d '\000')
echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/type 2>/dev/null)
echo NAME=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/name 2>/dev/null)
echo OCR=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/ocr 2>/dev/null)
echo CSD=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/csd 2>/dev/null)
echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)
echo PARENT=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent)
echo RATE=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate)
echo MIN=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_min_rate)
echo POSS=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_possible_parents)
dmesg | grep -E 'mmc1|21d60000' | head -25
echo BOOTCHK
