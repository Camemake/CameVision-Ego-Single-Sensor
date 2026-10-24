#!/bin/sh
# Official combo on leftover configured: UVC + UAC1, IAD, PID 0016.
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
A=$G/functions/uac1.gs0
# HS-only extras. Do not enable SS streaming (this kernel oopses).
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 2 > $U/uvc_num_request 2>/dev/null || true
rm -f $U/streaming/class/ss/h
# NV12 like usb_config.sh (kernel may require an uncompressed format)
NV=$U/streaming/uncompressed/u_nv12
if [ ! -d "$NV" ]; then
	mkdir -p $NV/1280_720p
	echo 1280 > $NV/1280_720p/wWidth
	echo 720 > $NV/1280_720p/wHeight
	echo 333333 > $NV/1280_720p/dwDefaultFrameInterval
	echo $((1280*720*20)) > $NV/1280_720p/dwMinBitRate
	echo $((1280*720*20)) > $NV/1280_720p/dwMaxBitRate
	echo $((1280*720*2)) > $NV/1280_720p/dwMaxVideoFrameBufferSize
	printf '333333\n666666\n1000000\n2000000\n' > $NV/1280_720p/dwFrameInterval
	echo 12 > $NV/bBitsPerPixel 2>/dev/null || true
	printf '%b' '\x4e\x56\x31\x32\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71' > $NV/guidFormat 2>/dev/null || true
	ln -s $NV $U/streaming/header/h/u 2>/dev/null || true
fi
# UAC1
mkdir -p $A
echo 3 > $A/p_chmask 2>/dev/null || true
echo 2 > $A/p_ssize 2>/dev/null || true
echo 3 > $A/c_chmask 2>/dev/null || true
echo 2 > $A/c_ssize 2>/dev/null || true
rm -f $C/f2
ln -s $A $C/f2
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
printf '0x0016' > $G/idProduct
echo Camemake > $G/strings/0x409/product
echo uvc_uac1 > $C/strings/0x409/configuration
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo F1=$(readlink $C/f1)
echo F2=$(readlink $C/f2)
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
