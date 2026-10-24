wget -q -O /userdata/camevision-ffs-uvc.py http://192.168.1.44:18765/camevision-ffs-uvc.py
wget -q -O /userdata/camevision-ffs-start.sh http://192.168.1.44:18765/camevision-ffs-start.sh
sed -i 's/\r$//' /userdata/camevision-ffs-uvc.py /userdata/camevision-ffs-start.sh
chmod 755 /userdata/camevision-ffs-uvc.py /userdata/camevision-ffs-start.sh
sh /userdata/camevision-ffs-start.sh
if [ -z "$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)" ]; then
	G=/sys/kernel/config/usb_gadget/rockchip
	C=$G/configs/b.1
	rm -f $C/f1
	ln -s $G/functions/ffs.adb $C/f1
	echo 0 > $G/bDeviceClass
	echo 0 > $G/bDeviceSubClass
	echo 0 > $G/bDeviceProtocol
	echo 0x0006 > $G/idProduct
	echo 21500000.usb > $G/UDC
	echo ADB_FALLBACK=$? STATE=$(cat /sys/class/udc/21500000.usb/state)
fi
