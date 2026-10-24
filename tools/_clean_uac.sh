#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
A=$G/functions/uac1.gs0
echo none > $G/UDC
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
sleep 1
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
sleep 1
echo AFTER_DWC STATE=$(cat /sys/class/udc/21500000.usb/state) UDCN=$(ls /sys/class/udc)
# Ensure links
rm -f $C/f1 $C/f2 $C/f3
ln -s $U $C/f1
ln -s $A $C/f2
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
printf '0x0016' > $G/idProduct
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo 21500000.usb > $G/UDC
echo UVC_BIND=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
if ! ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	echo FALLBACK_ADB
	echo none > $G/UDC
	rm -f $C/f1
	[ -e $C/f2 ] && rm -f $C/f2
	mkdir -p /dev/usb-ffs/adb
	mount | grep -q usb-ffs/adb || mount -o uid=2000,gid=2000 -t functionfs adb /dev/usb-ffs/adb
	pidof adbd >/dev/null || start-stop-daemon --start --quiet --background --exec /usr/bin/adbd
	ln -s $G/functions/ffs.adb $C/f2
	printf '0' > $G/bDeviceClass
	printf '0' > $G/bDeviceSubClass
	printf '0' > $G/bDeviceProtocol
	printf '0x0006' > $G/idProduct
	echo 21500000.usb > $G/UDC
	echo ADB_RC=$? STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC)
fi
dmesg | tail -10
