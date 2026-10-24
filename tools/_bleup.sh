#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
FW=/userdata/swt6621_fw
NAME="CameVision Ego Single Sensor"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/sv6160lite.nvbin"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SWT6621S_NV_SDIO.bin"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SEEKWAVE_NV_SWT6621S.bin"
printf '%s' "$FW" > /sys/module/firmware_class/parameters/path
rmmod skwbt 2>/dev/null || true
sleep 1
insmod /userdata/swt6621-rt52/skwbt.ko
sleep 1
hciconfig hci0 up
hciconfig hci0 name "$NAME"
hciconfig hci0 piscan
hciconfig hci0 leadv 3 2>/dev/null || hciconfig hci0 leadv 0 2>/dev/null || true
echo ===HCI===
hciconfig -a
echo ===DMESG===
dmesg | grep -iE 'skwbt|hci0|sv6160' | tail -12
echo ===WLAN===
ip -4 addr show wlan0 | grep inet
echo BLEUP_DONE
