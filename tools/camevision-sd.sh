#!/bin/sh
# Mount the microSD card on sdmmc0 (mmc1 / mmcblk1). Host I/O is 3.3 V.
# Only mount the partition. Do not probe the whole disk (a bad capacity
# can hang FAT/exFAT detection).
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
	if [ -b /dev/mmcblk1p1 ]; then
		mkdir -p "$MNT"
		if mount -t vfat -o utf8,flush /dev/mmcblk1p1 "$MNT" 2>>"$LOG"; then
			log "mounted /dev/mmcblk1p1 on $MNT"
			exit 0
		fi
	fi
	i=$((i + 1))
	sleep 1
done
log "no readable sd (mmcblk1p1)"
exit 1
