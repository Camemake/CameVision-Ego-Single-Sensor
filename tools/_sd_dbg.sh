#!/bin/sh
echo '=== dyn ==='
ls /sys/kernel/debug/dynamic_debug/control && echo dyn-yes
echo '=== mmc dbg ==='
ls /sys/module/mmc_core/parameters
echo '=== rescan ==='
ls /sys/class/mmc_host/mmc1
ls /sys/bus/platform/drivers/dwmmc_rockchip
echo '=== strings fifo ==='
grep -a -o 'fifo-mode\|use_internal_dma\|dw_mci_idmac\|pio_mode\|host->use_dma' /lib/modules/*/kernel/drivers/mmc/host/dw_mmc.ko 2>/dev/null | head
find /lib/modules -name 'dw_mmc*' 2>/dev/null
echo DBG
