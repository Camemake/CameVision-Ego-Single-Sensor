echo STILL_STUB
head -4 /etc/init.d/S50usbdevice
echo USBDEV
head -2 /usr/bin/usbdevice
ls /lib/udev/rules.d/61-usbdevice.rules* 2>/dev/null
echo INIT50
ls /etc/init.d/S50*
sync
reboot
