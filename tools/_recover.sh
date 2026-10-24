#!/bin/sh
# Restore a shell + SHARE BLE. Do not touch UVC. Do not run usb_config.sh.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
LOG=/userdata/wifi.log
NAME="CameVision Ego Single Sensor"
FW=/userdata/swt6621_fw
log() { echo "$(date +%T) $*" | tee -a "$LOG"; }

busybox telnetd -l /bin/sh -p 2323 2>/dev/null || telnetd -l /bin/sh -p 2323 2>/dev/null || true
log "telnetd :2323"

# Undo the UVC-session S50 stub if it persisted. Official ADB backup first.
if grep -q CV_S50_STUB /etc/init.d/S50usbdevice 2>/dev/null \
	|| [ "$(wc -l < /etc/init.d/S50usbdevice 2>/dev/null || echo 0)" -lt 15 ]; then
	if [ -f /userdata/cv-s50-bak/S50usbdevice ]; then
		mount -o remount,rw / 2>/dev/null || true
		cp -a /userdata/cv-s50-bak/S50usbdevice /etc/init.d/S50usbdevice
		chmod 755 /etc/init.d/S50usbdevice
		log "S50 restored from cv-s50-bak"
	fi
fi
if grep -q CV_USBDEVICE_STUB /usr/bin/usbdevice 2>/dev/null; then
	if [ -f /userdata/cv-s50-bak/usbdevice.official ]; then
		mount -o remount,rw / 2>/dev/null || true
		cp -a /userdata/cv-s50-bak/usbdevice.official /usr/bin/usbdevice
		chmod 755 /usr/bin/usbdevice
		log "usbdevice restored"
	fi
fi

# Combo VS6621: one antenna, SHARE NV
if [ -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" ]; then
	cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SWT6621S_NV_SDIO.bin"
	cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SEEKWAVE_NV_SWT6621S.bin"
	if [ -e /sys/module/firmware_class/parameters/path ]; then
		printf '%s' "$FW" > /sys/module/firmware_class/parameters/path
	fi
	log "NV=SHARE"
fi

insmod /userdata/swt6621-rt52/skwbt.ko 2>/dev/null || insmod /userdata/swt6621-rt52/skwbt_rt52.ko 2>/dev/null || true
sleep 1
hciconfig hci0 up 2>/dev/null || true
hciconfig hci0 name "$NAME" 2>/dev/null || true
hciconfig hci0 piscan 2>/dev/null || true
hciconfig hci0 leadv 3 2>/dev/null || hciconfig hci0 leadv 0 2>/dev/null || true
if hciconfig hci0 2>/dev/null | grep -q 'UP RUNNING'; then
	log "BLE_READY name=$NAME"
	echo BLE_OK
else
	log "BLE_WARN hci0 not UP — SHARE needs wifi reload later"
	echo BLE_NEED_RELOAD
fi
hciconfig -a 2>&1 | tail -20
ip -4 addr show wlan0 | grep inet
echo RECOVER_DONE
