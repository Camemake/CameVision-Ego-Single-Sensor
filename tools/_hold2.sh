#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ID=$(cat $G/idProduct)
echo F1=$(readlink $G/configs/b.1/f1)
echo DNAME=$(cat $G/functions/uvc.gs1/device_name)
echo FNAME=$(cat $G/functions/uvc.gs1/function_name)
echo VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/)
cat /sys/class/video4linux/video53/name
ps | grep -E 'uvc-bridge|single_live' | grep -v grep
echo ===BRIDGE===
tail -30 /userdata/cv-uvc-bridge.log
echo WLAN
ip -4 addr show wlan0 | grep inet
