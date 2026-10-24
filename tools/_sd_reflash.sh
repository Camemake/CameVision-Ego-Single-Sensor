#!/bin/sh
wget -q -O /tmp/camevision_boot_mono_wifi.img http://192.168.1.44:18766/camevision_boot_mono_wifi.img
SZ=$(wc -c < /tmp/camevision_boot_mono_wifi.img)
echo "boot $SZ"
[ "$SZ" -eq 11534336 ] || exit 3
dd if=/tmp/camevision_boot_mono_wifi.img of=/dev/mmcblk0p4 bs=65536 conv=fsync
sync
echo FLASH_SDHC
reboot
