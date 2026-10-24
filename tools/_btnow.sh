#!/bin/sh
echo ===WLAN===
ip -4 addr show wlan0 | grep inet
echo ===LSMOD===
lsmod | grep -E 'skw|swt|cfg80211|bluetooth|hci'
echo ===HCI===
hciconfig -a 2>&1
echo ===RFKILL===
rfkill list 2>/dev/null
echo ===FW===
ls -l /userdata/swt6621_fw/SWT6621S_NV_SDIO*.bin /lib/firmware/SWT6621S_NV_SDIO*.bin 2>/dev/null
md5sum /userdata/swt6621_fw/SWT6621S_NV_SDIO.bin /userdata/swt6621_fw/SWT6621S_NV_SDIO_ALONE.bin /userdata/swt6621_fw/SWT6621S_NV_SDIO_SHARE.bin 2>/dev/null
echo ===KO===
ls /userdata/swt6621-rt52/skwbt* /oem/usr/ko/skwbt* 2>/dev/null
echo ===WIFILOG===
grep -E 'BLE_|skwbt|hci|firmware|WIFI_READY' /userdata/wifi.log | tail -30
echo ===DMESG===
dmesg | grep -iE 'bluetooth|hci0|skwbt|sv6160|swt6621' | tail -25
echo ===NAME===
cat /etc/hostname 2>/dev/null
echo ===S40===
ls -l /etc/init.d/S40bluetoothd 2>/dev/null
head -20 /etc/init.d/S40bluetoothd 2>/dev/null
echo ===PS===
ps | grep -E 'bluetooth|hciattach|skwbt' | grep -v grep
