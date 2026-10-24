echo ===usbdevice===
ls -l /usr/bin/usbdevice /etc/init.d/S50usbdevice
head -5 /usr/bin/usbdevice
mount | grep usbdevice
echo ===udev===
grep -R usbdevice /etc/udev /lib/udev /usr/lib/udev 2>/dev/null | head -30
echo ===usb_config===
ls -l /tmp/.usb_config /etc/init.d/.usb_config /userdata/.usb_config /oem/etc/.usb_config 2>/dev/null
cat /usr/bin/usbdevice
echo ===s50start===
grep -n 'usb_adb_en\|USB_CONFIG\|usb_config\|FORCE\|echo usb' /etc/init.d/S50usbdevice | head -50
