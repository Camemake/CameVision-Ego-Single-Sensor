#!/bin/sh
# Live apply: combo SHARE NV + BLE name from V1.0. Reloads wifi — keep ADB.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
FW=/userdata/swt6621_fw
NAME="CameVision Ego Single Sensor"
LOG=/userdata/wifi.log
log() { echo "$(date +%T) $*" | tee -a "$LOG"; }

if [ ! -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" ]; then
	log "NO_SHARE_NV"
	exit 1
fi
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SWT6621S_NV_SDIO.bin"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SEEKWAVE_NV_SWT6621S.bin"
if [ -e /sys/module/firmware_class/parameters/path ]; then
	printf '%s' "$FW" > /sys/module/firmware_class/parameters/path
fi
mkdir -p /lib/firmware 2>/dev/null || true
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" /lib/firmware/SWT6621S_NV_SDIO.bin 2>/dev/null || true
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" /lib/firmware/SEEKWAVE_NV_SWT6621S.bin 2>/dev/null || true
log "NV now SHARE"

# If wifi is already up, only add BT. Reload wifi only if hci0 cannot start.
insmod /userdata/swt6621-rt52/skwbt.ko 2>/dev/null || insmod /userdata/swt6621-rt52/skwbt_rt52.ko 2>/dev/null || true
sleep 1
hciconfig hci0 up 2>/dev/null || true
if ! hciconfig hci0 2>/dev/null | grep -q 'UP RUNNING'; then
	log "hci0 not up on current firmware — will need wifi reload (SHARE)"
	echo NEED_RELOAD
else
	hciconfig hci0 name "$NAME"
	hciconfig hci0 piscan
	hciconfig hci0 leadv 3 2>/dev/null || hciconfig hci0 leadv 0 2>/dev/null || true
	log "BLE_READY name=$NAME"
	hciconfig -a
	echo BLE_OK
	exit 0
fi
echo TRY_SKWBT_DONE
hciconfig -a 2>&1 | tail -20
ip -4 addr show wlan0 | grep inet
