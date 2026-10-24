#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
echo ===before===
dmesg | grep -c BT_antenna
for v in share SHARE 1 2 "bt_antenna : share"; do
	echo "WRITE [$v]"
	printf '%s\n' "$v" > /proc/skwsdio/BT_ANT
	sleep 0.2
	echo -n "read="; cat /proc/skwsdio/BT_ANT; echo
	dmesg | grep -iE 'BT_antenna|bt_antenna|antenna' | tail -4
done
echo ===start bt===
printf 'start\n' > /proc/skwsdio/bt_service
sleep 2
echo -n "bt_service="; cat /proc/skwsdio/bt_service; echo
dmesg | tail -15
hciconfig hci0 up
hciconfig -a | head -16
echo ANTTRY_DONE
ip -4 addr show wlan0 | grep inet
