#!/bin/sh
# Mount the microSD card on sdmmc0 (mmc1 / mmcblk1). Host I/O is 3.3 V.
MNT=/mnt/sdcard
LOG=/userdata/sd-mount.log
: > "$LOG"
log() { echo "$(date +%T) $*" | tee -a "$LOG"; }

if mount | grep -q " $MNT "; then
	log "already $MNT"
	exit 0
fi

i=0
while [ "$i" -lt 8 ]; do
	for d in /dev/mmcblk1p1 /dev/mmcblk1; do
		[ -b "$d" ] || continue
		mkdir -p "$MNT"
		if mount -t vfat -o utf8,flush "$d" "$MNT" 2>>"$LOG" \
			|| mount -t exfat "$d" "$MNT" 2>>"$LOG" \
			|| mount "$d" "$MNT" 2>>"$LOG"; then
			log "mounted $d on $MNT"
			exit 0
		fi
	done
	i=$((i + 1))
	sleep 1
done
log "no readable sd (mmcblk1)"
exit 1
