#!/bin/sh
# Official usb_config UVC path without insmod/udev/SS streaming.
# Wi-Fi stays on wlan0. ConfigFS is remounted.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
echo none > $G/UDC 2>/dev/null || true
sleep 1
# Fresh configfs so f_uvc is not leftover-poisoned.
umount /sys/kernel/config 2>/dev/null || true
mkdir -p /sys/kernel/config
mount -t configfs none /sys/kernel/config 2>/dev/null || true
mkdir -p $G/strings/0x409
mkdir -p $G/configs/b.1/strings/0x409
mkdir -p $G/functions
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
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket
echo 2 > $U/uvc_num_request 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h
ln -s $U/control/header/h $U/control/class/ss/h
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth
echo 1600 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1400*1600*16*5)) > $_d/dwMinBitRate
echo $((1400*1600*16*30)) > $_d/dwMaxBitRate
echo $((1400*1600*2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n666666\n1000000\n2000000\n' > $_d/dwFrameInterval
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h
ln -s $U/streaming/header/h $U/streaming/class/hs/h
# UAC1 helper like usb_config.sh uac1
A=$G/functions/uac1.gs0
mkdir -p $A
echo 3 > $A/p_chmask 2>/dev/null || true
echo 2 > $A/p_ssize 2>/dev/null || true
echo 3 > $A/c_chmask 2>/dev/null || true
echo 2 > $A/c_ssize 2>/dev/null || true
ln -s $U $G/configs/b.1/f1
ln -s $A $G/configs/b.1/f2
UDC=$(ls /sys/class/udc | awk '{print $1}')
echo UDC_NAME=$UDC STATE=$(cat /sys/class/udc/$UDC/state)
echo $UDC > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/$UDC/state)
ls /sys/class/udc/$UDC/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
# If UVC failed, restore ADB gadget so USB is not left dead.
if ! ls /sys/class/udc/$UDC/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	echo FALLBACK_ADB
	echo none > $G/UDC 2>/dev/null || true
	rm -f $G/configs/b.1/f1 $G/configs/b.1/f2
	mkdir -p $G/functions/ffs.adb
	mkdir -p /dev/usb-ffs/adb
	mount | grep -q usb-ffs/adb || mount -o uid=2000,gid=2000 -t functionfs adb /dev/usb-ffs/adb
	pidof adbd >/dev/null || start-stop-daemon --start --quiet --background --exec /usr/bin/adbd
	ln -s $G/functions/ffs.adb $G/configs/b.1/f1
	echo 0 > $G/bDeviceClass
	echo 0 > $G/bDeviceSubClass
	echo 0 > $G/bDeviceProtocol
	echo 0x0006 > $G/idProduct
	echo $UDC > $G/UDC
	echo ADB_RC=$? STATE=$(cat /sys/class/udc/$UDC/state) UDC=$(cat $G/UDC)
fi
