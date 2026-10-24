G=/sys/kernel/config/usb_gadget/rockchip
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) ID=$(cat $G/idProduct)
echo F1=$(readlink $G/configs/b.1/f1)
echo F2=$(readlink $G/configs/b.1/f2)
# Make sure this is ADB-only
rm -f $G/configs/b.1/f1
printf '0x0006' > $G/idProduct
printf '0' > $G/bDeviceClass
printf '0' > $G/bDeviceSubClass
printf '0' > $G/bDeviceProtocol
echo disconnect > /sys/class/udc/21500000.usb/soft_connect
sleep 1
echo AFTER_SOFT STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
if [ -z "$(cat $G/UDC)" ]; then
	echo 21500000.usb > $G/UDC
	echo REBIND=$?
fi
echo FINAL STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) ID=$(cat $G/idProduct)
echo LIVE
ls -l /tmp/camevision-live.jpg 2>/dev/null
echo S50
head -3 /etc/init.d/S50usbdevice
echo S99
ls /etc/init.d/S99*
echo USBDEV
head -3 /usr/bin/usbdevice
