#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
echo ===USBDEVICE===
ls -l /usr/bin/usbdevice /userdata/cv-s50-bak/usbdevice.official
head -5 /usr/bin/usbdevice
echo ===S50===
ls -l /etc/init.d/S50usbdevice
echo ===USB_CFG===
cat /tmp/.usb_config
echo ===UDEV===
grep -R 'usbdevice\|S50usb' /etc/udev /lib/udev /oem 2>/dev/null | head -30
echo ===GADGET===
G=/sys/kernel/config/usb_gadget/rockchip
echo UDC=$(cat $G/UDC) ID=$(cat $G/idProduct) F1=$(readlink $G/configs/b.1/f1)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls $G/functions
echo ===PS===
ps | grep -E 'usbdevice|adbd|S50|udev' | grep -v grep
