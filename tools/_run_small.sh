wget -q -O /tmp/small.sh http://192.168.1.44:18765/_small.sh
sed -i 's/\r$//' /tmp/small.sh
sh /tmp/small.sh
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
	touch /userdata/camevision-am.on
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo BRIDGE $!
	sleep 1
	tail -20 /userdata/cv-uvc-bridge.log
else
	G=/sys/kernel/config/usb_gadget/rockchip
	C=$G/configs/b.1
	rm -f $C/f1
	printf '0' > $G/bDeviceClass
	printf '0' > $G/bDeviceSubClass
	printf '0' > $G/bDeviceProtocol
	printf '0x0006' > $G/idProduct
	echo 21500000.usb > $G/UDC
	echo ADB_FALLBACK=$? STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC)
fi
