# Careful Camemake bind: stop ADB, then UVC-only, never write descriptors while bound.
G=/sys/kernel/config/usb_gadget/rockchip
printf '%s\n' 'usb_adb_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
touch /userdata/camevision-am.on
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
wget -q -O /userdata/g.sh http://192.168.1.44:18765/g.sh
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py /userdata/g.sh
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
echo BRIDGE $!
echo BEFORE UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
/etc/init.d/S50usbdevice stop
echo AFTER_STOP UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
if [ -n "$(cat $G/UDC)" ]; then
	echo STOP_FAILED
	exit 1
fi
trap '' HUP
sh /userdata/g.sh
echo OK_DONE
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
ps | grep camevision-uvc-bridge | grep -v grep
tail -15 /userdata/cv-uvc-bridge.log
dmesg | tail -6
