mount -o remount,rw / 2>/dev/null || true
if [ -f /userdata/cv-s50-bak/S50usbdevice.official ]; then
	cp -a /userdata/cv-s50-bak/S50usbdevice.official /etc/init.d/S50usbdevice
elif [ -f /userdata/S50usbdevice ]; then
	cp -a /userdata/S50usbdevice /etc/init.d/S50usbdevice
fi
chmod 755 /etc/init.d/S50usbdevice
if [ -f /etc/init.d/S99camevision-uvc ]; then
	mv -f /etc/init.d/S99camevision-uvc /etc/init.d/S99camevision-uvc.off
fi
if [ -f /usr/bin/usbdevice.cvbak ]; then
	cp -a /usr/bin/usbdevice.cvbak /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
if [ -f /lib/udev/rules.d/61-usbdevice.rules.cvoff ]; then
	mv -f /lib/udev/rules.d/61-usbdevice.rules.cvoff /lib/udev/rules.d/61-usbdevice.rules
fi
echo RESTORED
head -4 /etc/init.d/S50usbdevice
head -2 /usr/bin/usbdevice
ls /etc/init.d/S50* /lib/udev/rules.d/61-usbdevice.rules*
sync
reboot
