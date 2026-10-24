mount -o remount,rw / 2>/dev/null || true
mkdir -p /userdata/cv-s50-bak
# Never leave S50 backups in init.d — rcS runs every S50*.
for f in /etc/init.d/S50usbdevice.cvbak /etc/init.d/S50usbdevice.cvpreuvc; do
	if [ -e "$f" ]; then
		mv -f "$f" /userdata/cv-s50-bak/
	fi
done
if [ ! -f /userdata/cv-s50-bak/S50usbdevice.official ]; then
	if grep -q configfs_init /etc/init.d/S50usbdevice; then
		cp -a /etc/init.d/S50usbdevice /userdata/cv-s50-bak/S50usbdevice.official
	fi
fi
printf '%s\n' \
'#!/bin/sh' \
'busybox telnetd -l /bin/sh -p 2323 2>/dev/null' \
'ifconfig lo up 2>/dev/null' \
'exit 0' > /etc/init.d/S50usbdevice
chmod 755 /etc/init.d/S50usbdevice
printf '%s\n' '#!/bin/sh' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
if [ -f /lib/udev/rules.d/61-usbdevice.rules ]; then
	mv -f /lib/udev/rules.d/61-usbdevice.rules /lib/udev/rules.d/61-usbdevice.rules.cvoff
fi
wget -q -O /userdata/camevision-uvc-first.sh http://192.168.1.44:18765/camevision-uvc-first.sh
wget -q -O /etc/init.d/S99camevision-uvc http://192.168.1.44:18765/S99camevision-uvc
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-first.sh /etc/init.d/S99camevision-uvc /userdata/camevision-uvc-bridge.py
chmod 755 /userdata/camevision-uvc-first.sh /etc/init.d/S99camevision-uvc
touch /userdata/camevision-am.on
echo INSTALLED
ls -l /etc/init.d/S50usbdevice /etc/init.d/S99camevision-uvc /userdata/camevision-uvc-first.sh
head -4 /etc/init.d/S50usbdevice
ls /etc/init.d/S50*
sync
sync
reboot
