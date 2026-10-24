#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
NAME="CameVision Ego Single Sensor"
echo ===stop leftover hci===
hciconfig hci0 down 2>/dev/null
rmmod skwbt
sleep 3
echo -n "bt_service="; cat /proc/skwsdio/bt_service; echo
echo stop > /proc/skwsdio/bt_service
sleep 1
echo start > /proc/skwsdio/bt_service
sleep 3
echo -n "bt_service="; cat /proc/skwsdio/bt_service; echo
dmesg | grep -iE 'skw_start_bt|boot bt|BTREADY|cp_state|cp not ready' | tail -10
echo ===insmod skwbt after service===
insmod /userdata/swt6621-rt52/skwbt.ko
sleep 2
hciconfig hci0 up
hciconfig hci0 name "$NAME"
hciconfig hci0 piscan
hciconfig hci0 leadv 3 2>/dev/null || true
hciconfig -a
dmesg | grep -iE 'download_nv|chip version|file load|Opcode' | tail -10
ip -4 addr show wlan0 | grep inet
echo BLEORDER_DONE
