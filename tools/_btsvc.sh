#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
echo ===FIND===
find /sys /proc /dev -iname '*bt*' 2>/dev/null | grep -iE 'skw|seek|serv|antenna|6160' | head -80
echo ===DEBUGFS===
find /sys/kernel/debug -iname '*skw*' -o -iname '*bt*' 2>/dev/null | head -40
echo ===PROC===
ls /proc/skw* /proc/*skw* /proc/*bt* 2>/dev/null
echo ===MISC===
ls /sys/class/misc 2>/dev/null
ls /sys/devices/virtual/misc 2>/dev/null
echo ===SDIO DRV===
ls /sys/bus/sdio/drivers 2>/dev/null
ls /sys/module/skw_sdio_lite/ 2>/dev/null
ls /sys/module/skw_sdio_lite/holders 2>/dev/null
cat /sys/module/skw_sdio_lite/refcnt
echo ===DMESG BT SVC===
dmesg | grep -iE 'BT SERIVCE|BT SERVICE|bt_antenna|BTREADY|BTBOOT|bt_start|SKW_BT' | tail -30
