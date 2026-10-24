#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
echo ===rfkill===
for d in /sys/class/rfkill/rfkill*; do
	echo "$d $(cat $d/name) state=$(cat $d/state) type=$(cat $d/type)"
done
echo 1 > /sys/class/rfkill/rfkill0/state
rfkill unblock all 2>/dev/null || true
echo ===gpio===
for n in 32 68 103 106 114; do
	if [ ! -d /sys/class/gpio/gpio$n ]; then
		echo $n > /sys/class/gpio/export 2>/dev/null || true
	fi
	if [ -f /sys/class/gpio/gpio$n/value ]; then
		echo gpio$n=$(cat /sys/class/gpio/gpio$n/value)
	else
		echo gpio$n=busy
	fi
done
echo 1 > /sys/class/gpio/gpio68/value 2>/dev/null || true
echo 1 > /sys/class/rkwifi/wifi_bt_vbat
# leave wifi_power as-is if already 1
cat /sys/class/rkwifi/wifi_power
echo 21f60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/unbind
sleep 1
echo 21f60000.mmc > /sys/bus/platform/drivers/dwmmc_rockchip/bind
sleep 4
echo ===sdio===
ls /sys/bus/sdio/devices 2>/dev/null
cat /sys/bus/sdio/devices/*/uevent 2>/dev/null
dmesg | tail -16
