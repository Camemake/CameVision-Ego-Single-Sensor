#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
echo ===READ===
echo -n "BT_ANT="; cat /proc/skwsdio/BT_ANT; echo
echo -n "BT_UART1="; cat /proc/skwsdio/BT_UART1; echo
echo -n "bt_service="; cat /proc/skwsdio/bt_service; echo
echo -n "wifi_service="; cat /proc/skwsdio/wifi_service; echo
echo -n "Version="; cat /proc/skwsdio/Version; echo
echo -n "profile="; cat /proc/skwsdio/profile; echo
echo ===SET SHARE===
echo share > /proc/skwsdio/BT_ANT
echo 1 > /proc/skwsdio/BT_ANT
echo ===AFTER===
echo -n "BT_ANT="; cat /proc/skwsdio/BT_ANT; echo
echo start > /proc/skwsdio/bt_service
echo 1 > /proc/skwsdio/bt_service
sleep 1
echo -n "bt_service="; cat /proc/skwsdio/bt_service; echo
dmesg | tail -25
echo ===HCI===
hciconfig -a
