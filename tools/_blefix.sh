#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
FW=/userdata/swt6621_fw
NAME="CameVision Ego Single Sensor"
printf '%s' "$FW" > /sys/module/firmware_class/parameters/path

echo ===params===
ls /sys/module/skwbt/parameters 2>/dev/null
ls /sys/module/swt6621s_wifi/parameters 2>/dev/null
ls /sys/module/skw_sdio_lite/parameters 2>/dev/null
for p in /sys/module/skwbt/parameters/* /sys/module/swt6621s_wifi/parameters/* /sys/module/skw_sdio_lite/parameters/*; do
	[ -f "$p" ] || continue
	echo "$p=$(cat $p 2>/dev/null)"
done

echo ===rfkill===
echo 1 > /sys/class/rfkill/rfkill0/state 2>/dev/null
echo 1 > /sys/class/rkwifi/wifi_bt_vbat 2>/dev/null

try_nv() {
	src="$1"
	echo "=== TRY $src ==="
	cp -f "$src" "$FW/sv6160lite.nvbin"
	cp -f "$src" "$FW/sv6160.nvbin"
	cp -f "$src" "$FW/sv6316.nvbin"
	hciconfig hci0 down 2>/dev/null
	rmmod skwbt 2>/dev/null
	sleep 2
	insmod /userdata/swt6621-rt52/skwbt.ko
	sleep 2
	hciconfig hci0 up
	if hciconfig hci0 2>/dev/null | grep -q 'UP RUNNING'; then
		hciconfig hci0 name "$NAME"
		hciconfig hci0 piscan
		hciconfig hci0 leadv 3 2>/dev/null || hciconfig hci0 leadv 0 2>/dev/null || true
		echo BLE_OK "$src"
		hciconfig -a
		return 0
	fi
	echo BLE_FAIL "$src"
	dmesg | grep -iE 'download_nv|sv6160|cp response|file load|hci0: Opcode' | tail -8
	return 1
}

try_nv "$FW/SWT6621S_NV_for_test_share.bin" && exit 0
try_nv "$FW/SWT6621S_NV_SDIO_SHARE.bin" && exit 0
try_nv "$FW/SWT6621S_SEEKWAVE_R00001.bin" && exit 0
try_nv "$FW/SWT6621S_NV_SDIO_ALONE.bin" && exit 0
echo BLE_ALL_FAIL
hciconfig -a
ip -4 addr show wlan0 | grep inet
