#!/bin/sh
echo "=== vmmc phandle ==="
hexdump -C /proc/device-tree/mmc@21d60000/vmmc-supply
hexdump -C /proc/device-tree/mmc@21d60000/vqmmc-supply
echo "=== regulators ==="
for d in /proc/device-tree/*sd* /proc/device-tree/*vcc*sd* /proc/device-tree/vcc*; do
  [ -d "$d" ] || continue
  echo "-- $d"
  ls "$d" | head
  [ -f "$d/regulator-name" ] && echo name=$(tr '\000' ' ' < "$d/regulator-name")
  [ -f "$d/gpio" ] && hexdump -C "$d/gpio"
  [ -f "$d/regulator-always-on" ] && echo always-on
done
ls /sys/class/regulator
for r in /sys/class/regulator/regulator.*; do
  n=$(cat $r/name 2>/dev/null)
  echo "$n $($r/microvolts 2>/dev/null) state=$(cat $r/state 2>/dev/null)"
done
echo VMMC
