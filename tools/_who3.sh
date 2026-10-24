echo UPTIME=$(cat /proc/uptime)
echo S50
head -8 /etc/init.d/S50usbdevice
echo USBDEV
head -2 /usr/bin/usbdevice
echo CFG
cat /tmp/.usb_config
lsattr /tmp/.usb_config 2>/dev/null
echo CALLERS
grep -R 'usb_config\|S50usbdevice\|idProduct\|usb_adb' /oem/usr/bin /usr/bin /etc/init.d /userdata /lib/udev 2>/dev/null | grep -v Binary | head -40
echo OEM
ls /oem/usr/bin/usb_config.sh /usr/bin/usb_config.sh 2>/dev/null
head -20 /oem/usr/bin/usb_config.sh 2>/dev/null
echo UDEV
ls /lib/udev/rules.d/*usb* /etc/udev/rules.d/* 2>/dev/null
cat /lib/udev/rules.d/61-usbdevice.rules.cvoff 2>/dev/null
echo PS
ps | grep -E 'usb|gadget|adbd' | grep -v grep
