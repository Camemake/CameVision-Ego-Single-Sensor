#!/bin/sh
# Debug why f_uvc gadget_start returns -19. Keep Wi-Fi. Restore FFS or ADB after.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo none > $G/UDC 2>/dev/null || true
kill $(ps | grep '[c]amevision-ffs-uvc.py' | awk '{print $1}') 2>/dev/null || true
# Enable verbose USB gadget logs
if [ -f /sys/kernel/debug/dynamic_debug/control ]; then
	echo 'file f_uvc.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'file uvc_v4l2.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'file configfs.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'file composite.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'file core.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'file udc-core.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'file gadget.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'func dwc3_gadget_start +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'func uvc_function_bind +p' > /sys/kernel/debug/dynamic_debug/control
	echo DYNDBG_OK
fi
# Completely unlink UVC from config
rm -f $C/f1 $C/f2 $C/f3
# Recreate a known-good official-style UVC (HS, MJPEG 1400x1600 only)
echo Camemake > $U/device_name 2>/dev/null || true
echo Camemake > $U/function_name 2>/dev/null || true
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 1 > $U/streaming_interval 2>/dev/null || true
echo 2 > $U/uvc_num_request 2>/dev/null || true
echo 0 > $U/streaming_bulk 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h 2>/dev/null || true
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
echo CTRL=$(ls $U/control/class)
echo STRM=$(ls $U/streaming/class)
echo FR=$(ls $U/streaming/mjpeg/m 2>/dev/null)
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
rm -f $U/streaming/class/ss/h
echo 239 > $G/bDeviceClass
echo 2 > $G/bDeviceSubClass
echo 1 > $G/bDeviceProtocol
echo 0x0016 > $G/idProduct
echo Camemake > $G/strings/0x409/product
echo high-speed > $G/max_speed 2>/dev/null || true
echo 0x0200 > $G/bcdUSB
ln -s $U $C/f1
echo LINKS f1=$(readlink $C/f1)
echo PRE_VIDEO
ls /sys/class/video4linux | wc -l
dmesg -c >/tmp/dmesg.pre 2>/dev/null || true
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
echo POST_VIDEO
for d in /sys/class/video4linux/video*; do
	n=$(cat $d/name 2>/dev/null)
	echo $d $n
done | grep -iE 'uvc|gadget|dummy|came' 
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo ---DMESG---
dmesg | tail -40
echo WLAN
ip -4 addr show wlan0 | grep inet
