#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
echo ===UVC===
echo UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ID=$(cat $G/idProduct) CLS=$(cat $G/bDeviceClass)
echo PROD=$(cat $G/strings/0x409/product)
echo F1=$(readlink $G/configs/b.1/f1)
echo DNAME=$(cat $G/functions/uvc.gs1/device_name)
echo FNAME=$(cat $G/functions/uvc.gs1/function_name)
ls -l /dev/video53
cat /sys/class/video4linux/video53/name
# Force host re-enumerate now that f_uvc is bound.
if [ -f /sys/class/udc/21500000.usb/soft_connect ]; then
	echo connect > /sys/class/udc/21500000.usb/soft_connect
	echo SOFT=$(cat /sys/class/udc/21500000.usb/soft_connect)
fi
sleep 1
echo AFTER_SOFT STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
# Start JPEG pump before Windows opens Camemake.
touch /userdata/camevision-am.on
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/camevision-uvc-bridge.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
echo BRIDGE=$!
sleep 1
echo ===BRIDGE===
tail -20 /userdata/cv-uvc-bridge.log
echo ===STATE===
echo STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo WLAN
ip -4 addr show wlan0 | grep inet
echo LIVE
ls -l /tmp/camevision-live.jpg
