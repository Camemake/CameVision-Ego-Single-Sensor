wget -q -O /tmp/fs.sh http://192.168.1.44:18765/_fs.sh
sed -i 's/\r$//' /tmp/fs.sh
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state)
sh /tmp/fs.sh
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	touch /userdata/camevision-am.on
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo BRIDGE $!
	sleep 2
	tail -20 /userdata/cv-uvc-bridge.log
else
	G=/sys/kernel/config/usb_gadget/rockchip
	rm -f $G/configs/b.1/f2
	echo high-speed > $G/max_speed 2>/dev/null || true
	echo 0x0200 > $G/bcdUSB
	echo 0x0006 > $G/idProduct
	echo 21500000.usb > $G/UDC
	echo ADB_FALLBACK=$? STATE=$(cat /sys/class/udc/21500000.usb/state)
fi
