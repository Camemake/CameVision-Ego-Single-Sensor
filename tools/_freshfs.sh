#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
echo none > $G/UDC 2>/dev/null || true
sleep 1
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
sleep 1
umount /sys/kernel/config
echo UMOUNT=$?
mkdir -p /sys/kernel/config
mount -t configfs none /sys/kernel/config
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
sleep 1
echo AFTER STATE=$(cat /sys/class/udc/21500000.usb/state) CFG=$(ls /sys/kernel/config/usb_gadget 2>/dev/null)
mkdir -p $G/strings/0x409
mkdir -p $G/configs/b.1/strings/0x409
echo 0x2207 > $G/idVendor
echo 0x0310 > $G/bcdDevice
echo 0x0200 > $G/bcdUSB
echo high-speed > $G/max_speed 2>/dev/null || true
echo 239 > $G/bDeviceClass
echo 2 > $G/bDeviceSubClass
echo 1 > $G/bDeviceProtocol
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo 500 > $G/configs/b.1/MaxPower
echo uvc > $G/configs/b.1/strings/0x409/configuration
echo 0x0016 > $G/idProduct
U=$G/functions/uvc.gs1
mkdir $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket
mkdir $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h
ln -s $U/control/header/h $U/control/class/ss/h
_d=$U/streaming/mjpeg/m/720p
mkdir -p $_d
echo 1280 > $_d/wWidth
echo 720 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1280*720*20)) > $_d/dwMinBitRate
echo $((1280*720*20)) > $_d/dwMaxBitRate
echo $((1280*720*2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n' > $_d/dwFrameInterval
mkdir $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h
ln -s $U/streaming/header/h $U/streaming/class/hs/h
A=$G/functions/uac1.gs0
mkdir $A
echo 3 > $A/p_chmask 2>/dev/null || true
echo 2 > $A/p_ssize 2>/dev/null || true
ln -s $U $G/configs/b.1/f1
ln -s $A $G/configs/b.1/f2
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
if ! ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	echo FALLBACK_ADB
	echo none > $G/UDC 2>/dev/null || true
	rm -f $G/configs/b.1/f1 $G/configs/b.1/f2
	mkdir $G/functions/ffs.adb
	mkdir -p /dev/usb-ffs/adb
	umount /dev/usb-ffs/adb 2>/dev/null || true
	mount -o uid=2000,gid=2000 -t functionfs adb /dev/usb-ffs/adb
	killall adbd 2>/dev/null || true
	start-stop-daemon --start --quiet --background --exec /usr/bin/adbd
	ln -s $G/functions/ffs.adb $G/configs/b.1/f1
	echo 0 > $G/bDeviceClass
	echo 0 > $G/bDeviceSubClass
	echo 0 > $G/bDeviceProtocol
	echo 0x0006 > $G/idProduct
	echo 21500000.usb > $G/UDC
	echo ADB_RC=$? STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC)
fi
echo WLAN
ip -4 addr show wlan0 | grep inet
