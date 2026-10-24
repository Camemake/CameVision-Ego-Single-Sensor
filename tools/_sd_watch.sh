#!/bin/sh
# Watch real cclk during a clean rebind. No kernel patches.
umount /mnt/sdcard 2>/dev/null
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind
sleep 1
# keep trying to set xin24m + 800 kHz while unbound
echo xin24m > /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent 2>/tmp/clk.err
echo 800000 > /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate 2>>/tmp/clk.err
echo UNBOUND_PARENT=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent)
echo UNBOUND_RATE=$(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate)
echo CLKERR=$(cat /tmp/clk.err)
# sample rates in background
: > /tmp/rates
(i=0; while [ $i -lt 80 ]; do
  echo $(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_parent) $(cat /sys/kernel/debug/clk/cclk_sdmmc0/clk_rate) >> /tmp/rates
  i=$((i+1))
done) &
echo 21d60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind
wait
echo "=== rates ==="
sort -u /tmp/rates
echo "=== dmesg ==="
dmesg | grep -E 'mmc1|21d60000' | tail -12
echo TYPE=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/type 2>/dev/null)
echo OCR=$(cat /sys/class/mmc_host/mmc1/mmc1:0001/ocr 2>/dev/null)
echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)
echo WATCH
