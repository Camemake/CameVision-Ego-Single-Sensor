#!/bin/sh
SER=$(cat /proc/device-tree/serial-number | tr -d '\000')
echo serial $SER
[ "$SER" = "e4feca993701b30c" ] || exit 2
sync
reboot
