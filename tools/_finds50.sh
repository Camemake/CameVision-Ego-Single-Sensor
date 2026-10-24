echo UPTIME=$(cat /proc/uptime)
echo S50HEAD
head -6 /etc/init.d/S50usbdevice
echo COPIES
ls -l /etc/init.d/S50usbdevice /etc/init.d/S50usbdevice.cvbak /userdata/S50usbdevice /oem/etc/init.d/S50usbdevice /oem/usr/bin/usb_config.sh 2>/dev/null
echo GREP
grep -R S50usbdevice /etc/init.d /userdata /oem /etc/profile /etc/inittab 2>/dev/null | grep -v Binary | head -30
echo S99
ls /etc/init.d/S99* /userdata/S99* 2>/dev/null
grep -n S50 /etc/init.d/S99* /userdata/S99* /userdata/camevision*.sh 2>/dev/null | head
