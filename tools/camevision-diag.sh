#!/bin/sh
# Board diagnostics. Read-only. Does not change USB gadget.
OUT=/userdata/diag.txt
: > "$OUT"
log() { echo "$*" | tee -a "$OUT"; }

log "=== CameVision diag $(date) ==="
log "uptime: $(cat /proc/uptime)"
log "model: $(cat /proc/device-tree/model 2>/dev/null | tr '\0' ' ')"
log "compat: $(cat /proc/device-tree/compatible 2>/dev/null | tr '\0' ' ')"
log "kernel: $(uname -a)"

log ""
log "=== USB gadget ==="
log "product=$(cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product 2>/dev/null)"
log "udc=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null)"
log "state=$(cat /sys/class/udc/21500000.usb/state 2>/dev/null)"
log "serial=$(cat /proc/cpuinfo | grep Serial)"

log ""
log "=== Wi-Fi ==="
log "chip=$(cat /proc/device-tree/wireless-wlan/wifi_chip_type 2>/dev/null | tr '\0' ' ')"
log "sdio:"
ls /sys/bus/sdio/devices 2>/dev/null | tee -a "$OUT" || log "(none)"
for u in /sys/bus/sdio/devices/*/uevent; do
	[ -f "$u" ] && grep -E 'SDIO_ID|SDIO_CLASS|MODALIAS' "$u" | tee -a "$OUT"
done
log "wlan0:"
ip -4 addr show wlan0 2>/dev/null | tee -a "$OUT" || log "(no wlan0)"
wpa_cli -i wlan0 status 2>/dev/null | grep -E 'wpa_state|ssid|ip_address' | tee -a "$OUT"

log ""
log "=== Camera ==="
log "i2c3:"
i2cdetect -y 3 2>/dev/null | tee -a "$OUT"
log "video:"
ls -l /dev/video* 2>/dev/null | tee -a "$OUT"
log "avdd=$(cat /sys/class/regulator/regulator.*/name 2>/dev/null | grep -n sc233 || true)"
for n in 8 9 134; do
	if [ -d /sys/class/gpio/gpio$n ]; then
		log "gpio$n=$(cat /sys/class/gpio/gpio$n/value) dir=$(cat /sys/class/gpio/gpio$n/direction)"
	else
		log "gpio$n=not-exported"
	fi
done

log ""
log "=== IMU ==="
ls /sys/bus/iio/devices/iio:device*/name 2>/dev/null | while read f; do
	log "$(dirname $f | xargs basename) $(cat $f)"
done
ls /sys/bus/spi/devices 2>/dev/null | tee -a "$OUT"

log ""
log "=== dmesg ==="
dmesg | grep -E 'mmc2|sdio|wlan|vs6621|sc233|lsm6|rkaiq|usb' | tail -40 | tee -a "$OUT"
log "DIAG_DONE"
cat "$OUT"
exit 0
