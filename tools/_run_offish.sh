wget -q -O /tmp/offish.sh http://192.168.1.44:18765/_offish.sh
sed -i 's/\r$//' /tmp/offish.sh
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
sh /tmp/offish.sh
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
	touch /userdata/camevision-am.on
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo BRIDGE $!
	sleep 1
	tail -25 /userdata/cv-uvc-bridge.log
fi
