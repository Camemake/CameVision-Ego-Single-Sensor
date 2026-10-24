#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ID=$(cat $G/idProduct)
echo F1=$(readlink $G/configs/b.1/f1)
echo DNAME=$(cat $G/functions/uvc.gs1/device_name)
echo MP=$(cat $G/functions/uvc.gs1/streaming_maxpacket)
echo HDR=$(ls $G/functions/uvc.gs1/streaming/header/h)
echo MJ=$(ls $G/functions/uvc.gs1/streaming/mjpeg/m)
echo NV=$(ls $G/functions/uvc.gs1/streaming/uncompressed 2>/dev/null)
echo VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
cat /sys/class/video4linux/video53/name 2>/dev/null
ps | grep -E 'uvc-bridge|single_live|adbd' | grep -v grep
echo ===LIVE===
ls -l /tmp/camevision-live.jpg
echo ===BRIDGE===
tail -40 /userdata/cv-uvc-bridge.log
echo WLAN
ip -4 addr show wlan0 | grep inet
