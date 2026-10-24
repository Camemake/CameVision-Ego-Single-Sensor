#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
touch /userdata/camevision-am.on
i=0
while [ $i -lt 40 ]; do
	if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
		break
	fi
	i=$((i + 1))
	sleep 1
done
if ! ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	echo NO_VIDEO >> /userdata/cv-uvc-pump.log
	exit 1
fi
if [ -s /userdata/camevision-uvc-bridge.py ]; then
	if ! ps | grep '[c]amevision-uvc-bridge.py' >/dev/null 2>&1; then
		: > /userdata/cv-uvc-bridge.log
		setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
		echo BRIDGE $! >> /userdata/cv-uvc-pump.log
	fi
fi
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ >> /userdata/cv-uvc-pump.log
cat /sys/kernel/config/usb_gadget/rockchip/idProduct >> /userdata/cv-uvc-pump.log
cat /sys/kernel/config/usb_gadget/rockchip/UDC >> /userdata/cv-uvc-pump.log
