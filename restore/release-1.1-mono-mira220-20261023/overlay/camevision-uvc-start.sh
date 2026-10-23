#!/bin/sh
# Start HS UVC named Camemake after Wi-Fi is up. Reboot returns to ADB-only.
export PATH=/oem/usr/bin:/usr/sbin:/sbin:/usr/bin:/bin:$PATH
LOG=/userdata/cv-uvc-start.log
log() { echo "$(date +%T) $*" | tee -a "$LOG"; }

: > "$LOG"
busybox telnetd -l /bin/sh -p 2323 2>/dev/null || true
log "telnetd :2323"

if ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
	:
elif [ ! -e /sys/bus/sdio/devices/mmc2:0001:1 ]; then
	log "no SDIO — skip wifi"
elif [ -x /userdata/camevision-wifi.sh ]; then
	log "starting wifi"
	/bin/sh /userdata/camevision-wifi.sh >>"$LOG" 2>&1 || true
fi

if ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
	ip -4 addr show wlan0 | grep inet | tee -a "$LOG"
	log "WIFI_OK"
else
	log "NO_WIFI — refuse UVC bind, keep ADB"
	exit 2
fi

if [ -x /userdata/_lock_uvc_safe.sh ]; then
	/bin/sh /userdata/_lock_uvc_safe.sh >>"$LOG" 2>&1 || {
		log "GADGET_FAIL"
		exit 3
	}
else
	log "missing /userdata/_lock_uvc_safe.sh"
	exit 3
fi

log "UVC_READY Camemake"
exit 0
