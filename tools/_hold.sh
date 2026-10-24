#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
echo UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ID=$(cat $G/idProduct) CLS=$(cat $G/bDeviceClass) F1=$(readlink $G/configs/b.1/f1)
echo DNAME=$(cat $G/functions/uvc.gs1/device_name)
echo VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
ls -l /dev/video53
ps | grep -E 'uvc-bridge|single_live|adbd' | grep -v grep
echo ===BRIDGE===
tail -40 /userdata/cv-uvc-bridge.log
echo ===S50===
head -2 /etc/init.d/S50usbdevice
echo WLAN
ip -4 addr show wlan0 | grep inet
