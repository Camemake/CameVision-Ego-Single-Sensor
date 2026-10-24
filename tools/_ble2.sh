#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
FW=/userdata/swt6621_fw
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/sv6160lite.nvbin"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/sv6160.nvbin"
printf '%s' "$FW" > /sys/module/firmware_class/parameters/path
ls -l "$FW/sv6160lite.nvbin"
hciconfig hci0 down 2>/dev/null
hciconfig hci1 down 2>/dev/null
rmmod skwbt 2>/dev/null
sleep 2
insmod /userdata/swt6621-rt52/skwbt.ko
sleep 2
hciconfig -a
dmesg | grep -iE 'skwbt|hci|sv6160|nvbin' | tail -20
echo BLE2_DONE
