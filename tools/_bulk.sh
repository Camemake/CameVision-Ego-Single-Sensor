#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo high-speed > $G/max_speed 2>/dev/null || true
echo 0x0200 > $G/bcdUSB
echo 1 > $U/streaming_bulk
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
# restore HS class links
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
echo none > $G/UDC
ln -s $U $C/f2
echo 0x0019 > $G/idProduct
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
