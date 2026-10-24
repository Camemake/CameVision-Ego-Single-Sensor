#!/bin/sh
ls /sys/class/mmc_host/mmc1/
ls /sys/kernel/debug/mmc1/ 2>/dev/null
cat /sys/kernel/debug/mmc1/ios 2>/dev/null
echo "---"
for f in /sys/class/mmc_host/mmc1/mmc1\:*/type /sys/class/mmc_host/mmc1/mmc1\:*/ocr /sys/class/mmc_host/mmc1/mmc1\:*/csd; do
  echo $f=$(cat "$f" 2>/dev/null)
done
echo SIZE=$(cat /sys/block/mmcblk1/size 2>/dev/null)
# host caps / ocr if exported
find /sys/class/mmc_host/mmc1 -maxdepth 2 -type f | head -40
echo OCRDUMP
