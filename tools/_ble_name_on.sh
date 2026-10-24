#!/bin/sh
cd /userdata
echo '=== show ==='
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Name|Alias|Powered|Discoverable|Pairable|Advertising|ActiveInstances|SupportedInstances|UUID' | head -40
echo '=== btmgmt ==='
btmgmt --help 2>&1 | head -5
which btmgmt 2>/dev/null
btmgmt advinfo 2>&1 | head -20
echo '=== instances ==='
ls /org/bluez 2>/dev/null
ls /sys/class/bluetooth/hci0 2>/dev/null | head
echo '=== logtail ==='
dmesg | grep -iE 'bluetooth|bluez|hci' | tail -8
echo DIAG
