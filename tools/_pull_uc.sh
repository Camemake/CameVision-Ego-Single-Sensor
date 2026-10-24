#!/bin/sh
echo ===UC_HEAD===
sed -n '1,180p' /oem/usr/bin/usb_config.sh
echo ===UC_TAIL===
sed -n '240,391p' /oem/usr/bin/usb_config.sh
echo ===KO===
ls /oem/usr/ko/usb_f_*.ko 2>/dev/null
echo ===USB_CONFIG_FILE===
cat /tmp/.usb_config 2>/dev/null
echo ===S50===
grep -n 'usb_uvc\|UVC_EN\|uvc.gs' /etc/init.d/S50usbdevice | head
echo ===INIT===
ls /etc/init.d/S50* /etc/init.d/S99*
