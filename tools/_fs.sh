#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
# Full-speed only: drop HS/SS class links so dwc3 does not need isoc-HS.
rm -f $U/control/class/ss/h
rm -f $U/streaming/class/hs/h
rm -f $U/streaming/class/ss/h
[ -e $U/control/class/fs/h ] || ln -s $U/control/header/h $U/control/class/fs/h
[ -e $U/streaming/class/fs/h ] || ln -s $U/streaming/header/h $U/streaming/class/fs/h
echo full-speed > $G/max_speed 2>/dev/null || true
echo 0x0110 > $G/bcdUSB
echo 512 > $U/streaming_maxpacket 2>/dev/null || true
echo none > $G/UDC
rm -f $C/f2
ln -s $U $C/f2
echo 0x0019 > $G/idProduct
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
