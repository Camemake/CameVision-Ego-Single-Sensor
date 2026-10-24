mount -o remount,rw / || true
mkdir -p /userdata/cv-s50-bak
# rcS runs every S99* including .off — move leftovers out of init.d
for f in /etc/init.d/S99camevision-uvc.off /etc/init.d/S99camevision-uvc; do
	[ -e "$f" ] && mv -f "$f" /userdata/cv-s50-bak/
done
# Restore official ADB-only S50 (boot default stays ADB).
if [ -f /userdata/cv-s50-bak/S50usbdevice.official ]; then
	cp -a /userdata/cv-s50-bak/S50usbdevice.official /etc/init.d/S50usbdevice
	sed -i 's/\r$//' /etc/init.d/S50usbdevice
	chmod 755 /etc/init.d/S50usbdevice
fi
# Stub usbdevice so udev DISCONNECTED cannot rebuild the gadget.
if [ -w /usr/bin/usbdevice ]; then
	if ! grep -q 'CV_USBDEVICE_STUB' /usr/bin/usbdevice; then
		cp -a /usr/bin/usbdevice /userdata/cv-s50-bak/usbdevice.official
	fi
	printf '%s\n' '#!/bin/sh' '# CV_USBDEVICE_STUB' 'exit 0' > /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
echo INITD
ls /etc/init.d/S50* /etc/init.d/S99*
echo USBDEV
head -3 /usr/bin/usbdevice
echo ---udc---
ls /sys/class/udc/21500000.usb/
echo ---udc-files---
for x in state is_selfpowered is_a_peripheral is_otg current_speed maximum_speed srp a_alt_hnp_support b_hnp_enable function; do
	echo -n "$x="; cat /sys/class/udc/21500000.usb/$x 2>/dev/null; echo
done
echo ---dev---
ls /sys/devices/platform/21500000.usb/ 2>/dev/null
echo ---role---
ls /sys/class/usb_role /sys/class/dual_role_usb /sys/class/typec 2>/dev/null
find /sys -name 'usb_role' -o -name 'soft_connect' -o -name 'mode' -o -name 'dr_mode' 2>/dev/null | grep -E 'usb|dwc|2150' | head -40
echo ---dr---
cat /sys/devices/platform/21500000.usb/dr_mode 2>/dev/null
cat /sys/firmware/devicetree/base/usb@21500000/dr-mode 2>/dev/null; echo
echo ---toggle ADB pullup---
G=/sys/kernel/config/usb_gadget/rockchip
echo none > $G/UDC
echo AFTER_NONE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC)
sleep 1
# ADB-only still linked on f2
echo 0x0006 > $G/idProduct
printf '21500000.usb' > $G/UDC
echo TOGGLE_RC=$?
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo UDC=$(cat $G/UDC)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
dmesg | tail -10
