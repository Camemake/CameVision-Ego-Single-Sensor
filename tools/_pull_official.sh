#!/bin/sh
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
echo ===WLAN===
ip -4 addr show wlan0 | grep inet
echo ===UDC===
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo MAXSPD=$(cat /sys/class/udc/21500000.usb/maximum_speed)
echo FUNC=$(cat /sys/class/udc/21500000.usb/function)
echo ===GADGET===
G=/sys/kernel/config/usb_gadget/rockchip
echo ID=$(cat $G/idProduct) CLS=$(cat $G/bDeviceClass)/$(cat $G/bDeviceSubClass)/$(cat $G/bDeviceProtocol)
echo MAX_SPEED_ATTR=$(cat $G/max_speed 2>/dev/null)
echo PROD=$(cat $G/strings/0x409/product)
echo LINKS
ls -l $G/configs/b.1/ | grep -E 'f[0-9]|ffs|uvc|uac'
echo ===FUNCS===
ls $G/functions
echo ===UVC_GS===
for U in $G/functions/uvc.gs1 $G/functions/uvc.gs6; do
	[ -d "$U" ] || continue
	echo -- $U
	echo CTRL=$(ls $U/control/class 2>/dev/null)
	echo STRM=$(ls $U/streaming/class 2>/dev/null)
	echo FS=$(ls $U/control/class/fs 2>/dev/null)
	echo HS=$(ls $U/control/class/hs 2>/dev/null)
	echo SS=$(ls $U/control/class/ss 2>/dev/null)
	echo SFS=$(ls $U/streaming/class/fs 2>/dev/null)
	echo SHS=$(ls $U/streaming/class/hs 2>/dev/null)
	echo SSS=$(ls $U/streaming/class/ss 2>/dev/null)
	echo MP=$(cat $U/streaming_maxpacket 2>/dev/null)
	echo BULK=$(cat $U/streaming_bulk 2>/dev/null)
	echo DNAME=$(cat $U/device_name 2>/dev/null)
	echo FNAME=$(cat $U/function_name 2>/dev/null)
	echo MJ=$(ls $U/streaming/mjpeg/m 2>/dev/null)
	echo HDR=$(ls $U/streaming/header/h 2>/dev/null)
done
echo ===USB_CONFIG===
wc -l /oem/usr/bin/usb_config.sh
grep -n 'streaming_maxpacket\|class/ss\|class/hs\|class/fs\|uvc.gs\|idProduct\|bDeviceClass\|device_name\|mkdir.*uvc\|ADB_ENABLE\|uac1' /oem/usr/bin/usb_config.sh | head -80
echo ===RKLUNCH===
ls -l /usr/bin/RkLunch* /oem/usr/bin/RkLunch* 2>/dev/null
head -60 /oem/usr/bin/RkLunch-UVC_TINY.sh 2>/dev/null
echo ===PS===
ps | grep -E 'ffs-uvc|adbd|single_live|rk_mpi|usbdevice' | grep -v grep
echo ===LIVE===
ls -l /tmp/camevision-live.jpg
echo ===DMESG===
dmesg | grep -E 'uvc_function|failed to start|UDC core|Unable to allocate|f_uvc' | tail -20
