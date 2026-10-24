mount -o remount,rw / 2>/dev/null || true
mkdir -p /userdata/cv-s50-bak
for f in /etc/init.d/S50usbdevice.cvbak /etc/init.d/S50usbdevice.cvpreuvc; do
	if [ -e "$f" ]; then
		mv -f "$f" /userdata/cv-s50-bak/
	fi
done
if [ ! -f /userdata/cv-s50-bak/S50usbdevice.official ]; then
	cp -a /etc/init.d/S50usbdevice /userdata/cv-s50-bak/S50usbdevice.official
fi
wget -q -O /etc/init.d/S50usbdevice http://192.168.1.44:18765/S50usbdevice.camemake
wget -q -O /etc/init.d/S99camevision-uvc http://192.168.1.44:18765/S99camevision-uvc
wget -q -O /userdata/camevision-uvc-pump.sh http://192.168.1.44:18765/camevision-uvc-pump.sh
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /etc/init.d/S50usbdevice /etc/init.d/S99camevision-uvc /userdata/camevision-uvc-pump.sh /userdata/camevision-uvc-bridge.py
chmod 755 /etc/init.d/S50usbdevice /etc/init.d/S99camevision-uvc /userdata/camevision-uvc-pump.sh
touch /userdata/camevision-am.on
echo INSTALLED
head -5 /etc/init.d/S50usbdevice
grep -n 'class/ss\|1400 1600\|usb_uvc_en\|Camemake' /etc/init.d/S50usbdevice
ls /etc/init.d/S50*
sync
sync
reboot
