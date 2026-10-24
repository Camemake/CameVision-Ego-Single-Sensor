# Re-apply restart no-op if the full S50 came back after panic.
mount -o remount,rw / 2>/dev/null || true
if ! grep -q CV_NO_RESTART /etc/init.d/S50usbdevice; then
	sed -i 's/^restart|reload)/restart|reload)\n	exit 0\n	# CV_NO_RESTART/' /etc/init.d/S50usbdevice
fi
printf '%s\n' '#!/bin/sh' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
wget -q -O /tmp/ok.sh http://192.168.1.44:18765/_ok.sh
sed -i 's/\r$//' /tmp/ok.sh
trap '' HUP
sh /tmp/ok.sh
echo STILL
sleep 4
G=/sys/kernel/config/usb_gadget/rockchip
echo ID=$(cat $G/idProduct)
echo UDC=$(cat $G/UDC)
echo F1=$(readlink $G/configs/b.1/f1)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/
ps | grep camevision-uvc-bridge | grep -v grep
tail -20 /userdata/cv-uvc-bridge.log
echo UPTIME=$(cat /proc/uptime)
