mount -o remount,rw / 2>/dev/null || true
mkdir -p /userdata/cv-s50-bak
mv -f /etc/init.d/S50usbdevice.cvbak /userdata/cv-s50-bak/ 2>/dev/null || true
mv -f /etc/init.d/S50usbdevice.cvpreuvc /userdata/cv-s50-bak/ 2>/dev/null || true
# keep stub
printf '%s\n' \
'#!/bin/sh' \
'busybox telnetd -l /bin/sh -p 2323 2>/dev/null' \
'ifconfig lo up 2>/dev/null' \
'exit 0' > /etc/init.d/S50usbdevice
chmod 755 /etc/init.d/S50usbdevice
# neutralize ADB restorer
if [ -f /userdata/camevision-uvc-stop.sh ]; then
	mv -f /userdata/camevision-uvc-stop.sh /userdata/camevision-uvc-stop.sh.off
fi
echo INIT
ls /etc/init.d/S50*
head -5 /etc/init.d/S50usbdevice
sync
sync
reboot
