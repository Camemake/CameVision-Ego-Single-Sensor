#!/bin/sh
mount -t debugfs debugfs /sys/kernel/debug 2>/dev/null
echo 'file sd.c +p' > /sys/kernel/debug/dynamic_debug/control 2>/dev/null
echo 'file mmc.c +p' > /sys/kernel/debug/dynamic_debug/control 2>/dev/null
echo 'file dw_mmc.c +p' > /sys/kernel/debug/dynamic_debug/control 2>/dev/null
echo 'func mmc_send_if_cond +p' > /sys/kernel/debug/dynamic_debug/control 2>/dev/null
echo 'func __mmc_send_if_cond +p' > /sys/kernel/debug/dynamic_debug/control 2>/dev/null
echo 'func mmc_sd_get_cid +p' > /sys/kernel/debug/dynamic_debug/control 2>/dev/null
grep -E 'send_if_cond|sd_get_cid|CMD8|if_cond' /sys/kernel/debug/dynamic_debug/control | head
umount /mnt/sdcard 2>/dev/null
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind
sleep 1
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind
sleep 3
dmesg | tail -40
echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:b368/type 2>/dev/null)
echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)
echo DBG
