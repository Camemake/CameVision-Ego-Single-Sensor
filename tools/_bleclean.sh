#!/bin/sh
# Clean VS6621 reload: SHARE antenna, then BT service, then skwbt.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
FW=/userdata/swt6621_fw
KO=/userdata/swt6621-rt52
NAME="CameVision Ego Single Sensor"
printf '%s' "$FW" > /sys/module/firmware_class/parameters/path
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SWT6621S_NV_SDIO.bin"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/SEEKWAVE_NV_SWT6621S.bin"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/sv6160lite.nvbin"
cp -f "$FW/SWT6621S_NV_SDIO_SHARE.bin" "$FW/sv6160.nvbin"

mkdir -p /data
echo share > /data/BT_ANT
echo share > /data/bt_antenna
echo 1 > /data/BT_ANT
echo 1 > /data/bt_antenna
ls -l /data

killall wpa_supplicant 2>/dev/null || true
hciconfig hci0 down 2>/dev/null
rmmod skwbt 2>/dev/null
rmmod swt6621s_wifi 2>/dev/null
rmmod skw_sdio_lite 2>/dev/null
sleep 2

insmod $KO/skw_sdio_lite.ko
sleep 1
echo share > /proc/skwsdio/BT_ANT 2>/dev/null
echo 1 > /proc/skwsdio/BT_ANT 2>/dev/null
echo ===BOOT===
dmesg | grep -iE 'BT_antenna|bt_antenna|BT_ANT|SHARE|ALONE' | tail -10
echo -n "BT_ANT="; cat /proc/skwsdio/BT_ANT; echo
ls -l /data

insmod $KO/swt6621s_wifi.ko
sleep 2
ip link set wlan0 up
wpa_supplicant -B -i wlan0 -c /userdata/wpa_camevision.conf -D nl80211
sleep 8
udhcpc -i wlan0 -n -q -t 8 2>/dev/null || true
ip -4 addr show wlan0 | grep inet

echo start > /proc/skwsdio/bt_service
sleep 2
echo -n "bt_service="; cat /proc/skwsdio/bt_service; echo
dmesg | grep -iE 'bt_service|BT SERIVCE|BT SERVICE|boot bt|BTREADY' | tail -12

insmod $KO/skwbt.ko
sleep 2
hciconfig hci0 up
hciconfig hci0 name "$NAME"
hciconfig hci0 piscan
hciconfig hci0 leadv 3 2>/dev/null || true
echo ===HCI===
hciconfig -a
dmesg | grep -iE 'download_nv|file load|hci0: Opcode|BLE_OK|chip version' | tail -12
echo BLECLEAN_DONE
