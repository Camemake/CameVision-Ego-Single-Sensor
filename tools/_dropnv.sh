#!/bin/sh
# Drop NV12 from the live gadget so Windows Camera must use MJPEG.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
U=$G/functions/uvc.gs1
C=$G/configs/b.1
kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
sleep 1
echo none > $G/UDC
echo > $G/UDC 2>/dev/null || true
sleep 1
echo AFTER_NONE UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
rm -f $U/streaming/header/h/u
echo HDR=$(ls $U/streaming/header/h)
echo 1 > $U/streaming/mjpeg/m/bDefaultFrameIndex 2>/dev/null || true
echo 21500000.usb > $G/UDC
echo BIND_RC=$? UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
echo VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
if ! ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	echo UVC_FAIL
	exit 2
fi
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
echo BRIDGE=$!
sleep 1
tail -12 /userdata/cv-uvc-bridge.log
echo HOLD STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) HDR=$(ls $U/streaming/header/h)
