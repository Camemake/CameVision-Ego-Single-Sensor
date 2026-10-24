#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
FW=/userdata/swt6621_fw
KO=/userdata/swt6621-rt52
printf '%s' "$FW" > /sys/module/firmware_class/parameters/path
lsmod | grep -E 'skw|swt'
echo ===dmesg===
dmesg | tail -20
if [ ! -d /sys/class/net/wlan0 ]; then
	insmod $KO/cfg80211.ko 2>/dev/null
	insmod $KO/mac80211.ko 2>/dev/null
	insmod $KO/skw_sdio_lite.ko 2>/dev/null
	sleep 1
	insmod $KO/swt6621s_wifi.ko 2>/dev/null
	sleep 2
fi
ip link set wlan0 up
killall wpa_supplicant 2>/dev/null
wpa_supplicant -B -i wlan0 -c /userdata/wpa_camevision.conf -D nl80211
n=0
while [ $n -lt 20 ]; do
	st=$(wpa_cli -i wlan0 status 2>/dev/null | grep wpa_state= | cut -d= -f2)
	echo wpa_state=$st
	[ "$st" = "COMPLETED" ] && break
	sleep 1
	n=$((n + 1))
done
udhcpc -i wlan0 -n -q -t 8
ip -4 addr show wlan0 | grep inet
echo WIFI_BACK
