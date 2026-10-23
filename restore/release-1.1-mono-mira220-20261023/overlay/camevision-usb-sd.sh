#!/bin/sh
# Export the microSD over USB mass-storage while a host is plugged in
# and nothing is recording. Give the card back to Linux otherwise.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
LUN=$G/functions/mass_storage.0/lun.0/file
UDC=/sys/class/udc/21500000.usb/state
MNT=/mnt/sdcard
DEV=/dev/mmcblk1p1
LOG=/userdata/cv-usb-sd.log

log() { echo "$(date +%T) $*" >> "$LOG"; }

lun_set() {
	[ -e "$LUN" ] || return 1
	printf '%s' "$1" > "$LUN" 2>/dev/null || echo "$1" > "$LUN"
}

lun_clear() {
	[ -e "$LUN" ] || return 0
	printf '' > "$LUN" 2>/dev/null || echo > "$LUN"
}

card_mounted() {
	grep -q " $MNT " /proc/mounts
}

host_here() {
	st=$(cat "$UDC" 2>/dev/null)
	[ "$st" = configured ] || [ "$st" = attached ]
}

export_card() {
	[ -b "$DEV" ] || return 1
	[ -e "$LUN" ] || return 1
	if [ -f /tmp/camevision-record.on ]; then
		return 1
	fi
	if card_mounted; then
		sync
		umount "$MNT" || return 1
	fi
	if card_mounted; then
		log "busy $MNT"
		return 1
	fi
	lun_set "$DEV" || return 1
	log "MSC $DEV"
	return 0
}

return_card() {
	lun_clear
	if [ -b "$DEV" ] && ! card_mounted; then
		mkdir -p "$MNT"
		PART=/dev/mmcblk1p1
		[ -b "$PART" ] || PART=$DEV
		mount -t vfat -o utf8,flush "$PART" "$MNT" 2>/dev/null && log "MNT $MNT"
	fi
}

log start
while true; do
	if [ ! -e "$LUN" ]; then
		sleep 2
		continue
	fi
	if host_here && [ ! -f /tmp/camevision-record.on ]; then
		got=$(cat "$LUN" 2>/dev/null)
		if [ -z "$got" ]; then
			export_card || true
		elif card_mounted; then
			sync
			umount "$MNT" || log "busy $MNT"
		fi
	else
		got=$(cat "$LUN" 2>/dev/null)
		if [ -n "$got" ] || ! card_mounted; then
			return_card
		fi
	fi
	sleep 1
done
