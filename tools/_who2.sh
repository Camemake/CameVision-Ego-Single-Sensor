echo ===udev===
grep -R S50usbdevice /lib/udev /etc/udev /usr/lib/udev 2>/dev/null
grep -R usb_config /lib/udev /etc/udev 2>/dev/null | head
echo ===scripts===
grep -l usb_adb_en /etc/init.d/* /userdata/* /oem/usr/bin/* /usr/bin/* 2>/dev/null
echo ===s50start-callers===
grep -R 'S50usbdevice start' /etc /oem /userdata /usr/bin /lib 2>/dev/null | head -20
echo ===usbdevice-bin===
head -2 /usr/bin/usbdevice
ls /lib/udev/rules.d/61-usbdevice.rules*
echo ===init===
ls /etc/init.d/S*usb* /etc/init.d/S99* /etc/init.d/S80* 2>/dev/null
echo ===cv===
grep -n usb_adb_en /userdata/*.sh /userdata/*.py /etc/init.d/S99* 2>/dev/null | head
echo ===usb_config===
ls -l /oem/usr/bin/usb_config.sh /usr/bin/usb_config.sh 2>/dev/null
echo ===uptime===
cat /proc/uptime
