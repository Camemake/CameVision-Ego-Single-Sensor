#!/bin/sh
# Tear down FunctionFS + dwc3, delete leftover gadgets, bind Camemake first.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
killall adbd 2>/dev/null || true
umount /dev/usb-ffs/adb 2>/dev/null || true
umount /dev/usb-ffs/ntb 2>/dev/null || true

destroy_uvc() {
	_u=$1
	[ -d "$_u" ] || return 0
	rm -f $_u/streaming/class/fs/h $_u/streaming/class/hs/h $_u/streaming/class/ss/h
	rm -f $_u/streaming/header/h/m $_u/streaming/header/h/u $_u/streaming/header/h/f
	rmdir $_u/streaming/header/h 2>/dev/null || true
	for d in $_u/streaming/mjpeg/m/* $_u/streaming/uncompressed/u/* $_u/streaming/framebased/f/*; do
		[ -d "$d" ] && rmdir "$d" 2>/dev/null || true
	done
	rmdir $_u/streaming/mjpeg/m $_u/streaming/mjpeg 2>/dev/null || true
	rmdir $_u/streaming/uncompressed/u $_u/streaming/uncompressed 2>/dev/null || true
	rmdir $_u/streaming/framebased/f $_u/streaming/framebased 2>/dev/null || true
	rm -f $_u/control/class/fs/h $_u/control/class/hs/h $_u/control/class/ss/h
	rmdir $_u/control/header/h 2>/dev/null || true
	rmdir $_u 2>/dev/null || true
}
destroy_g() {
	_g=$1
	[ -d "$_g" ] || return 0
	printf none > $_g/UDC 2>/dev/null || true
	rm -f $_g/configs/b.1/f1 $_g/configs/b.1/f2 $_g/configs/b.1/f3 $_g/os_desc/b.1
	destroy_uvc $_g/functions/uvc.gs1
	destroy_uvc $_g/functions/uvc.gs6
	for f in $_g/functions/*; do
		rmdir $f 2>/dev/null || true
	done
	rmdir $_g/configs/b.1/strings/0x409 2>/dev/null || true
	rmdir $_g/configs/b.1 2>/dev/null || true
	rmdir $_g/strings/0x409 2>/dev/null || true
	rmdir $_g 2>/dev/null || true
}

echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
n=0
while [ $n -lt 25 ]; do
	[ ! -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
echo UDC_GONE
destroy_g /sys/kernel/config/usb_gadget/camemake
destroy_g /sys/kernel/config/usb_gadget/rockchip
echo LEFT
ls /sys/kernel/config/usb_gadget/ 2>/dev/null || echo NO_GADGETS

echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
n=0
while [ $n -lt 40 ]; do
	[ -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
sleep 1
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls -l /sys/class/udc/21500000.usb/gadget 2>/dev/null || echo NO_GADGET_SYMLINK

G=/sys/kernel/config/usb_gadget/camemake
mkdir -p $G/strings/0x409
mkdir -p $G/configs/b.1/strings/0x409
printf '0x2207' > $G/idVendor
printf '0x0016' > $G/idProduct
printf '0x0200' > $G/bcdUSB
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
echo high-speed > $G/max_speed 2>/dev/null || true
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo 500 > $G/configs/b.1/MaxPower
echo uvc > $G/configs/b.1/strings/0x409/configuration
U=$G/functions/uvc.gs1
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h
ln -s $U/control/header/h $U/control/class/hs/h 2>/dev/null || true
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth
echo 1600 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1400 * 1600 * 16 * 5)) > $_d/dwMinBitRate
echo $((1400 * 1600 * 16 * 30)) > $_d/dwMaxBitRate
echo $((1400 * 1600 * 2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n' > $_d/dwFrameInterval
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h
ln -s $U/streaming/header/h $U/streaming/class/hs/h
ln -s $U $G/configs/b.1/f1
printf '21500000.usb' > $G/UDC
echo YANK_RC $?
echo UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
tail -12 /userdata/cv-uvc-bridge.log
dmesg | tail -8
echo UPTIME=$(cat /proc/uptime)
