mount -o remount,rw / 2>/dev/null || true
if [ -f /userdata/cv-s50-bak/S50usbdevice.official ]; then
	cp -a /userdata/cv-s50-bak/S50usbdevice.official /etc/init.d/S50usbdevice
elif [ -f /userdata/S50usbdevice ]; then
	cp -a /userdata/S50usbdevice /etc/init.d/S50usbdevice
fi
chmod 755 /etc/init.d/S50usbdevice
# Keep restart from fighting after we switch.
if ! grep -q CV_NO_RESTART /etc/init.d/S50usbdevice; then
	sed -i 's/^restart|reload)/restart|reload)\n	exit 0\n	# CV_NO_RESTART/' /etc/init.d/S50usbdevice
fi
# Do not first-bind UVC at boot (that -19s the UDC).
if [ -f /etc/init.d/S99camevision-uvc ]; then
	mv -f /etc/init.d/S99camevision-uvc /etc/init.d/S99camevision-uvc.off
fi
printf '%s\n' '#!/bin/sh' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
echo RECIPE_S50
head -5 /etc/init.d/S50usbdevice
ls /etc/init.d/S50* /etc/init.d/S99camevision-uvc*
sync
reboot
