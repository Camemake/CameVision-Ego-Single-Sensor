echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ---off---
head -30 /etc/init.d/S99camevision-uvc.off
echo ---ego---
head -20 /etc/init.d/S99ego-stereo
echo ---who-first---
grep -n 'uvc-first\|uvc-start\|g.sh\|0016' /etc/init.d/S99* /userdata/camevision-single.sh /userdata/camevision-uvc-start.sh 2>/dev/null | head -40
echo ---move-off---
mkdir -p /userdata/cv-s50-bak
mv -f /etc/init.d/S99camevision-uvc.off /userdata/cv-s50-bak/ 2>/dev/null || true
# neutralize usbdevice so DISCONNECTED does not rebuild ADB-only / UVC
if ! grep -q 'CV_USBDEVICE_STUB' /usr/bin/usbdevice; then
	cp -a /usr/bin/usbdevice /userdata/cv-s50-bak/usbdevice.official
	printf '%s\n' '#!/bin/sh' '# CV_USBDEVICE_STUB' 'exit 0' > /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
echo USBDEV
head -3 /usr/bin/usbdevice
ls /etc/init.d/S99*
echo ADBD; ps | grep '[a]dbd'
