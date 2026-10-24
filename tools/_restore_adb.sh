G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
echo none > /sys/kernel/config/usb_gadget/camemake/UDC 2>/dev/null || true
echo none > $G/UDC 2>/dev/null || true
rm -f $C/f1 $C/f2 $C/f3
mkdir -p $G/functions/ffs.adb
mkdir -p /dev/usb-ffs/adb
umount /dev/usb-ffs/adb 2>/dev/null || true
mount -o uid=2000,gid=2000 -t functionfs adb /dev/usb-ffs/adb
killall adbd 2>/dev/null || true
start-stop-daemon --start --quiet --background --exec /usr/bin/adbd
sleep 1
ln -s $G/functions/ffs.adb $C/f1
echo 0x0006 > $G/idProduct
echo 0 > $G/bDeviceClass
echo 0 > $G/bDeviceSubClass
echo 0 > $G/bDeviceProtocol
echo 21500000.usb > $G/UDC
echo ADB_RC=$? STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) ID=$(cat $G/idProduct)
echo disconnect > /sys/class/udc/21500000.usb/soft_connect
sleep 1
if [ -z "$(cat $G/UDC)" ]; then
	echo 21500000.usb > $G/UDC
fi
echo FINAL STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) UDC=$(cat $G/UDC)
# restore official usbdevice so unplug brings ADB back
if [ -f /userdata/cv-s50-bak/usbdevice.official ]; then
	cp -a /userdata/cv-s50-bak/usbdevice.official /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
echo USBDEV
head -3 /usr/bin/usbdevice
echo LIVE
ls -l /tmp/camevision-live.jpg
echo WLAN
ip -4 addr show wlan0 | grep inet
