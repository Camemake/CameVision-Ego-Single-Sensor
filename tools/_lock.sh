mount -o remount,rw / 2>/dev/null || true
if [ ! -f /usr/bin/usbdevice.cvbak ]; then
	cp -a /usr/bin/usbdevice /usr/bin/usbdevice.cvbak
fi
printf '%s\n' '#!/bin/sh' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
if [ -f /lib/udev/rules.d/61-usbdevice.rules ]; then
	mv -f /lib/udev/rules.d/61-usbdevice.rules /lib/udev/rules.d/61-usbdevice.rules.cvoff
	udevadm control --reload 2>/dev/null || true
fi
# Stop S50 restart from rebuilding ADB if anything still calls it.
if ! grep -q 'CV_NO_RESTART' /etc/init.d/S50usbdevice; then
	cp -a /etc/init.d/S50usbdevice /etc/init.d/S50usbdevice.cvbak
	sed -i 's/^restart|reload)/restart|reload)\n	# CV_NO_RESTART\n	exit 0/' /etc/init.d/S50usbdevice
fi
printf '%s\n' 'usb_adb_en' 'usb_uvc_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
touch /userdata/camevision-am.on
echo LOCK_OK
head -2 /usr/bin/usbdevice
ls /lib/udev/rules.d/61-usbdevice.rules* 2>/dev/null
grep -n CV_NO_RESTART /etc/init.d/S50usbdevice
cat /tmp/.usb_config
