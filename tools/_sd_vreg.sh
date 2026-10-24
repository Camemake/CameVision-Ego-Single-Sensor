#!/bin/sh
echo '=== regulators ==='
for d in /sys/class/regulator/regulator.*; do
	n=$(cat "$d/name" 2>/dev/null)
	s=$(cat "$d/state" 2>/dev/null)
	v=$(cat "$d/microvolts" 2>/dev/null)
	e=$(cat "$d/enable" 2>/dev/null)
	echo "$d $n v=$v state=$s en=$e"
done
echo VREG
