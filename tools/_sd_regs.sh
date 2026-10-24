#!/bin/sh
# Dump sdmmc0 vs emmc host regs and card identity. Do not touch Wi-Fi mmc2.
echo "=== ios mmc1 ==="
cat /sys/kernel/debug/mmc1/ios 2>/dev/null || cat /sys/kernel/debug/mmc1/ios
ls /sys/kernel/debug/mmc1/
echo "=== card ==="
for f in type name preferred_erase_size cid csd ocr rca scr date fwrev hwrev manfid oemid serial; do
  echo -n "$f="
  cat /sys/class/mmc_host/mmc1/mmc1:0001/$f 2>/dev/null
done
echo "size=$(cat /sys/block/mmcblk1/size 2>/dev/null)"
echo "=== dt clocks ==="
hexdump -C /proc/device-tree/mmc@21d60000/clocks
hexdump -C /proc/device-tree/mmc@21d60000/clock-names
hexdump -C /proc/device-tree/mmc@21d60000/rockchip,default-sample-phase
ls /proc/device-tree/mmc@21d60000/rockchip,use-v2-tuning && echo v2yes
hexdump -C /proc/device-tree/mmc@21d60000/compatible
echo "=== clk ==="
for c in cclk_sdmmc0 hclk_sdmmc0; do
  echo "-- $c"
  cat /sys/kernel/debug/clk/$c/clk_rate
  cat /sys/kernel/debug/clk/$c/clk_phase 2>/dev/null
  cat /sys/kernel/debug/clk/$c/clk_duty_cycle 2>/dev/null
done
echo REGS
