#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
echo MOUNT
mount | grep config
# Unbind every gadget
for u in /sys/kernel/config/usb_gadget/*/UDC; do
	[ -e "$u" ] && echo none > "$u"
done
sleep 1
# Unlink functions
for c in /sys/kernel/config/usb_gadget/*/configs/*/f[0-9]*; do
	[ -e "$c" ] && rm -f "$c"
done
# Best-effort destroy uvc functions
for U in /sys/kernel/config/usb_gadget/*/functions/uvc.*; do
	[ -d "$U" ] || continue
	rm -f $U/streaming/class/fs/h $U/streaming/class/hs/h $U/streaming/class/ss/h
	rm -f $U/streaming/header/h/m $U/streaming/header/h/u $U/streaming/header/h/f1 $U/streaming/header/h/f2
	rmdir $U/streaming/header/h 2>/dev/null
	rm -rf $U/streaming/mjpeg/m $U/streaming/uncompressed $U/streaming/framebased 2>/dev/null
	rm -f $U/control/class/fs/h $U/control/class/ss/h $U/control/class/hs/h
	rmdir $U/control/header/h 2>/dev/null
	rmdir $U 2>/dev/null
	echo LEFT_U=$(ls -d $U 2>/dev/null)
done
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
sleep 1
umount /sys/kernel/config
echo UMOUNT=$?
ls /sys/kernel/config 2>/dev/null
mount -t configfs none /sys/kernel/config
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
sleep 1
echo AFTER
ls /sys/kernel/config/usb_gadget 2>/dev/null
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
# Fresh Camemake UVC+UAC1
G=/sys/kernel/config/usb_gadget/camemake
mkdir -p $G/strings/0x409
mkdir -p $G/configs/c.1/strings/0x409
echo 0x2207 > $G/idVendor
echo 0x0016 > $G/idProduct
echo 0x0200 > $G/bcdUSB
echo 0x0310 > $G/bcdDevice
echo high-speed > $G/max_speed 2>/dev/null || true
echo 239 > $G/bDeviceClass
echo 2 > $G/bDeviceSubClass
echo 1 > $G/bDeviceProtocol
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo 500 > $G/configs/c.1/MaxPower
echo uvc > $G/configs/c.1/strings/0x409/configuration
U=$G/functions/uvc.0
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
A=$G/functions/uac1.0
mkdir $A
echo 3 > $A/p_chmask 2>/dev/null || true
ln -s $U $G/configs/c.1/f1
ln -s $A $G/configs/c.1/f2
echo LINKS
ls -l $G/configs/c.1/
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
echo VIDEO
find /sys -name 'video4linux' 2>/dev/null
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -10
echo WLAN
ip -4 addr show wlan0 | grep inet
