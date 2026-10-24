wget -q -O /tmp/nuke.sh http://192.168.1.44:18765/_nuke.sh
sed -i 's/\r$//' /tmp/nuke.sh
sh /tmp/nuke.sh
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	echo GOT_GADGET_VIDEO
	ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/
	kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
	touch /userdata/camevision-am.on
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo BRIDGE $!
	sleep 1
	tail -20 /userdata/cv-uvc-bridge.log
fi
