echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo F1=$(readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1)
echo F2=$(readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2)
echo LIVE
ls -l /tmp/camevision-live.jpg
echo DMESG
dmesg | grep -E 'uvc_function|failed to start|gadget.0' | tail -20
# restore official usbdevice
if [ -f /userdata/cv-s50-bak/usbdevice.official ]; then
	cp -a /userdata/cv-s50-bak/usbdevice.official /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
echo USBDEV
head -3 /usr/bin/usbdevice
echo S50
head -4 /etc/init.d/S50usbdevice
echo WLAN
ip -4 addr show wlan0 | grep inet
