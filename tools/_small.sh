#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs2
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket
echo 2 > $U/uvc_num_request 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h 2>/dev/null || true
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
_d=$U/streaming/mjpeg/m/720p
mkdir -p $_d
echo 1280 > $_d/wWidth
echo 720 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1280*720*20)) > $_d/dwMinBitRate
echo $((1280*720*20)) > $_d/dwMaxBitRate
echo $((1280*720*2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n666666\n1000000\n2000000\n' > $_d/dwFrameInterval
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
echo PREPARED720
echo none > $G/UDC
rm -f $C/f1
ln -s $U $C/f1
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
printf '0x0016' > $G/idProduct
echo Camemake > $G/strings/0x409/product
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -6
