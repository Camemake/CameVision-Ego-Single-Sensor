#!/bin/sh
echo '=== mounts ==='
mount | grep -iE 'sd|mmc|card|userdata|oem' || true
echo '=== block ==='
ls -l /dev/mmcblk* /dev/sd* 2>/dev/null || true
cat /proc/partitions
echo '=== mmc ==='
ls -l /sys/block/mmcblk* 2>/dev/null
ls /sys/bus/mmc/devices 2>/dev/null
echo '=== df ==='
df -h
echo '=== camevision ==='
ls -la /userdata/camevision 2>/dev/null | head
ls -la /mnt/sdcard 2>/dev/null | head
ls -la /mnt/sd 2>/dev/null | head
ls -la /media 2>/dev/null | head
echo '=== status ==='
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo '=== ble log ==='
tail -20 /userdata/camevision-agent.log
echo '=== ble-io ==='
tail -20 /userdata/ble-io.log 2>/dev/null || true
grep -E 'BLE_WRITE|BLE_CMD|BLE_NOTIFY' /userdata/camevision-agent.log | tail -20
echo SD
