#!/bin/sh
echo '=== regs ==='
for d in /sys/class/regulator/regulator.*; do
	n=$(cat $d/name 2>/dev/null)
	echo "$n $($d/microvolts 2>/dev/null) state=$(cat $d/state 2>/dev/null)"
done | grep -iE 'sd|vcc3|mmc'
echo '=== mmc supply ==='
ls -l /sys/devices/platform/21d60000.mmc/ | head
find /sys/devices/platform/21d60000.mmc -name 'microvolts' -o -name 'state' 2>/dev/null | head
echo PWR
