mount -o remount,rw / 2>/dev/null || true
test -f /etc/init.d/S50usbdevice.cvbak || cp -a /etc/init.d/S50usbdevice /etc/init.d/S50usbdevice.cvbak
printf '%s\n' '#!/bin/sh' 'case "$1" in' 'stop)' 'echo none > /sys/kernel/config/usb_gadget/rockchip/UDC' ';;' 'esac' 'exit 0' > /etc/init.d/S50usbdevice
chmod 755 /etc/init.d/S50usbdevice
printf '%s\n' '#!/bin/sh' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
printf '%s\n' 'usb_adb_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
chattr +i /tmp/.usb_config 2>/dev/null || true
echo LOCK2_OK
cat /etc/init.d/S50usbdevice
head -2 /usr/bin/usbdevice
cat /tmp/.usb_config
