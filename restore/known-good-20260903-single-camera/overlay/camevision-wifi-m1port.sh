#!/bin/sh
# Portable factory-M1 Wi-Fi bring-up. No Efference binaries, no efr-vendor-get.
# Source: S25_efference_wlan on the M1 system_a donor.
#
# Gate: SDIO function 1FFE:6621 must already be on mmc2 (DT pwrseq).
# Modules: /userdata/swt6621-rt52 or /ko (same names as factory /ko).
# Firmware: SWT6621S_NV_SDIO.bin at firmware_class path (ALONE renamed).

KO=/userdata/swt6621-rt52
[ -d "$KO" ] || KO=/ko
FW_SRC=$KO/vs6621_fw
[ -d "$FW_SRC" ] || FW_SRC=/userdata/swt6621_fw
FW_DST=/lib/firmware
WLAN=wlan0

start() {
	ip link show $WLAN >/dev/null 2>&1 && return 0

	cat /sys/bus/sdio/devices/*/uevent 2>/dev/null | grep -q "1FFE:6621" || {
		echo "M1PORT: VS6621 SDIO device not found, skipping"
		return 1
	}

	echo "M1PORT: initializing VS6621 WiFi"

	if [ -d "$FW_SRC" ]; then
		if [ ! -f "$FW_SRC/SWT6621S_NV_SDIO.bin" ] && [ -f "$FW_SRC/SWT6621S_NV_SDIO_ALONE.bin" ]; then
			cp -f "$FW_SRC/SWT6621S_NV_SDIO_ALONE.bin" "$FW_SRC/SWT6621S_NV_SDIO.bin"
		fi
		if [ -e /sys/module/firmware_class/parameters/path ]; then
			printf '%s' "$FW_SRC" > /sys/module/firmware_class/parameters/path
		fi
		mkdir -p "$FW_DST" 2>/dev/null && cp -f "$FW_SRC"/* "$FW_DST"/ 2>/dev/null || true
	fi

	# Factory order (insmod_wifi.sh vs6621 block). Extra crypto kos optional.
	insmod $KO/cfg80211.ko 2>/dev/null
	insmod $KO/libarc4.ko 2>/dev/null
	insmod $KO/mac80211.ko 2>/dev/null
	insmod $KO/ctr.ko 2>/dev/null
	insmod $KO/ccm.ko 2>/dev/null
	insmod $KO/aes_generic.ko 2>/dev/null
	insmod $KO/skw_sdio_lite.ko 2>/dev/null
	sleep 0.2
	insmod $KO/swt6621s_wifi.ko 2>/dev/null
	sleep 0.2
	insmod $KO/skwbt.ko 2>/dev/null

	mkdir -p /var/run/wpa_supplicant
	WPA_CONF=/tmp/m1port-wpa.conf
	if [ -f /userdata/wpa_camevision.conf ]; then
		WPA_CONF=/userdata/wpa_camevision.conf
	else
		printf 'ctrl_interface=/var/run/wpa_supplicant\nupdate_config=1\n' > "$WPA_CONF"
	fi
	wpa_supplicant -B -i $WLAN -c "$WPA_CONF" -D nl80211 >/dev/null 2>&1
	echo "M1PORT: VS6621 WiFi init done"
}

stop() {
	killall wpa_supplicant 2>/dev/null
	sleep 0.5
	rmmod skwbt 2>/dev/null
	rmmod swt6621s_wifi 2>/dev/null
	rmmod skw_sdio_lite 2>/dev/null
	rmmod mac80211 2>/dev/null
	rmmod cfg80211 2>/dev/null
	rmmod libarc4 2>/dev/null
	rmmod aes_generic 2>/dev/null
	rmmod ccm 2>/dev/null
	rmmod ctr 2>/dev/null
}

case "$1" in
	start|"") start ;;
	stop) stop ;;
	restart) stop; sleep 1; start ;;
	*) echo "Usage: $0 {start|stop|restart}"; exit 1 ;;
esac
exit 0
