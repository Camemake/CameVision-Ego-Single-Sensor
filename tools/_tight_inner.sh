#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo none > $G/UDC
# Official S50 put ADB on f1. Keep it, add UVC as f2.
[ -e $C/f1 ] || ln -s $G/functions/ffs.adb $C/f1
ln -s $U $C/f2
echo 0x0019 > $G/idProduct
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo F1=$(readlink $C/f1)
echo F2=$(readlink $C/f2)
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
