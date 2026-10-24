wget -q -O /tmp/tight.sh http://192.168.1.44:18765/_tight_inner.sh
sed -i 's/\r$//' /tmp/tight.sh
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) F=$(ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1)
sh /tmp/tight.sh
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	touch /userdata/camevision-am.on
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo BRIDGE $!
	sleep 2
	tail -25 /userdata/cv-uvc-bridge.log
else
	G=/sys/kernel/config/usb_gadget/rockchip
	rm -f $G/configs/b.1/f2
	echo 0x0006 > $G/idProduct
	echo 21500000.usb > $G/UDC
	echo ADB_FALLBACK=$? STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC)
fi
