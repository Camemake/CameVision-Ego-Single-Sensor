#!/bin/sh
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind 2>/dev/null
sleep 1
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind
sleep 3
echo "=== card ==="
cat /sys/class/mmc_host/mmc1/mmc1:0001/type 2>/dev/null
cat /sys/block/mmcblk1/size 2>/dev/null
dmesg | grep -E 'mmc1|21d60000' | tail -15
echo "=== syms ==="
grep -E 'dw_mci_setup_bus|dw_mci_set_ios|dw_mci_rk|rockchip.*ios|mmc_set_ios|mmc_send_if_cond|mmc_go_idle|mmc_sd_init' /proc/kallsyms
echo "=== clk parent ==="
ls /sys/kernel/debug/clk/cclk_sdmmc0/
cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent 2>/dev/null
cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_possible_parents 2>/dev/null
cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_min_rate 2>/dev/null
cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_max_rate 2>/dev/null
echo SYMS_OK
