#!/bin/sh
# Recover the slot, then identify from xin24m so 400 kHz is real.
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind 2>/dev/null
sleep 1
echo PARENT_BEFORE=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent)
echo RATE_BEFORE=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate)
echo xin24m > /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent
echo 800000 > /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate
echo PARENT=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent)
echo RATE=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate)
echo POSS=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_possible_parents)
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind
sleep 5
echo PARENT_AFTER=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent)
echo RATE_AFTER=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate)
dmesg | grep -E 'mmc1|21d60000' | tail -20
echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/type 2>/dev/null)
echo OCR=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/ocr 2>/dev/null)
echo CSD=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/csd 2>/dev/null)
echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)
echo XIN24
