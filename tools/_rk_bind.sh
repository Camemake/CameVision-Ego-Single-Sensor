#!/bin/sh
# Bind official UVC onto the now-idle UDC. Do not dwc3-reset again.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
F=$G/functions
C=$G/configs/b.1
LOG=/userdata/cv-rk-uvc.log
: > $LOG
log() { echo "$*" | tee -a $LOG; }

ip -4 addr show wlan0 | grep -q '192.168.1.72' || { log 'NO_WIFI'; exit 1; }

log ===NOW===
log CFG=$(mount | grep configfs)
log GADGETS=$(ls /sys/kernel/config/usb_gadget)
log UDC=$(cat $G/UDC 2>/dev/null)
log STATE=$(cat /sys/class/udc/21500000.usb/state)
log FUNCS=$(ls $F 2>/dev/null)
log LINKS=$(ls $C 2>/dev/null)
log ADB=$(pidof adbd)
log USBDEV=$(ps | grep '[u]sbdevice')

# If S50 recreated ADB, unlink it. Keep gadget dir.
rm -f $C/f1 $C/f2 $C/f3 $C/f4 $C/ffs.adb
killall adbd 2>/dev/null || true
umount /dev/usb-ffs/adb 2>/dev/null || true

mkdir -p $G/strings/0x409
mkdir -p $C/strings/0x409
echo 0x2207 > $G/idVendor
echo 0x0310 > $G/bcdDevice
echo 0x0200 > $G/bcdUSB
echo 239 > $G/bDeviceClass
echo 2 > $G/bDeviceSubClass
echo 1 > $G/bDeviceProtocol
echo 0x0016 > $G/idProduct
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo 500 > $C/MaxPower
echo uvc > $C/strings/0x409/configuration
echo high-speed > $G/max_speed 2>/dev/null || true

UVC_GS=uvc.gs1
UVC_NAME=Camemake
mkdir -p ${F}/$UVC_GS
echo $UVC_NAME > ${F}/$UVC_GS/device_name
echo $UVC_NAME > ${F}/$UVC_GS/function_name
echo 3072 > ${F}/$UVC_GS/streaming_maxpacket
echo 2 > ${F}/$UVC_GS/uvc_num_request

mkdir -p ${F}/$UVC_GS/control/header/h
[ -e ${F}/$UVC_GS/control/class/fs/h ] || ln -s ${F}/$UVC_GS/control/header/h ${F}/$UVC_GS/control/class/fs/h
[ -e ${F}/$UVC_GS/control/class/ss/h ] || ln -s ${F}/$UVC_GS/control/header/h ${F}/$UVC_GS/control/class/ss/h
mkdir -p ${F}/$UVC_GS/streaming/header/h

configure_uvc_resolution_nv12() {
	W=$1; H=$2
	D=${F}/$UVC_GS/streaming/uncompressed/u_nv12/${W}_${H}p
	mkdir -p $D
	echo $W > $D/wWidth
	echo $H > $D/wHeight
	echo 333333 > $D/dwDefaultFrameInterval
	echo $((W*H*20)) > $D/dwMinBitRate
	echo $((W*H*20)) > $D/dwMaxBitRate
	echo $((W*H*2)) > $D/dwMaxVideoFrameBufferSize
	echo -e "333333\n666666\n1000000\n2000000" > $D/dwFrameInterval
	echo 12 > ${F}/$UVC_GS/streaming/uncompressed/u_nv12/bBitsPerPixel
	echo -ne \\x4e\\x56\\x31\\x32\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/uncompressed/u_nv12/guidFormat
}
configure_uvc_resolution_mjpeg() {
	W=$1; H=$2
	D=${F}/$UVC_GS/streaming/mjpeg/m/${W}_${H}p
	mkdir -p $D
	echo $W > $D/wWidth
	echo $H > $D/wHeight
	echo 333333 > $D/dwDefaultFrameInterval
	echo $((W*H*20)) > $D/dwMinBitRate
	echo $((W*H*20)) > $D/dwMaxBitRate
	echo $((W*H*2)) > $D/dwMaxVideoFrameBufferSize
	echo -e "333333\n666666\n1000000\n2000000" > $D/dwFrameInterval
	echo -ne \\x4d\\x4a\\x50\\x47\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/mjpeg/m/guidFormat
}
configure_uvc_resolution_h264() {
	W=$1; H=$2
	D=${F}/$UVC_GS/streaming/framebased/f1/${W}_${H}p
	mkdir -p $D
	echo $W > $D/wWidth
	echo $H > $D/wHeight
	echo 333333 > $D/dwDefaultFrameInterval
	echo $((W*H*10)) > $D/dwMinBitRate
	echo $((W*H*10)) > $D/dwMaxBitRate
	echo -e "333333\n400000\n500000\n666666\n1000000\n2000000" > $D/dwFrameInterval
	echo -ne \\x48\\x32\\x36\\x34\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/framebased/f1/guidFormat
}
configure_uvc_resolution_h265() {
	W=$1; H=$2
	D=${F}/$UVC_GS/streaming/framebased/f2/${W}_${H}p
	mkdir -p $D
	echo $W > $D/wWidth
	echo $H > $D/wHeight
	echo 333333 > $D/dwDefaultFrameInterval
	echo $((W*H*10)) > $D/dwMinBitRate
	echo $((W*H*10)) > $D/dwMaxBitRate
	echo -e "333333\n400000\n500000\n666666" > $D/dwFrameInterval
	echo -ne \\x48\\x32\\x36\\x35\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/framebased/f2/guidFormat
}

mkdir -p ${F}/$UVC_GS/streaming/uncompressed/u_nv12
configure_uvc_resolution_nv12 1280 720
configure_uvc_resolution_nv12 1920 1080
[ -e ${F}/$UVC_GS/streaming/header/h/u ] || ln -s ${F}/$UVC_GS/streaming/uncompressed/u_nv12 ${F}/$UVC_GS/streaming/header/h/u

mkdir -p ${F}/$UVC_GS/streaming/mjpeg/m
configure_uvc_resolution_mjpeg 1024 768
configure_uvc_resolution_mjpeg 1920 1080
configure_uvc_resolution_mjpeg 1400 1600
[ -e ${F}/$UVC_GS/streaming/header/h/m ] || ln -s ${F}/$UVC_GS/streaming/mjpeg/m ${F}/$UVC_GS/streaming/header/h/m

mkdir -p ${F}/$UVC_GS/streaming/framebased/f1
configure_uvc_resolution_h264 1280 720
configure_uvc_resolution_h264 1920 1080
[ -e ${F}/$UVC_GS/streaming/header/h/f1 ] || ln -s ${F}/$UVC_GS/streaming/framebased/f1 ${F}/$UVC_GS/streaming/header/h/f1

mkdir -p ${F}/$UVC_GS/streaming/framebased/f2
configure_uvc_resolution_h265 1280 720
configure_uvc_resolution_h265 1920 1080
[ -e ${F}/$UVC_GS/streaming/header/h/f2 ] || ln -s ${F}/$UVC_GS/streaming/framebased/f2 ${F}/$UVC_GS/streaming/header/h/f2

[ -e ${F}/$UVC_GS/streaming/class/fs/h ] || ln -s ${F}/$UVC_GS/streaming/header/h ${F}/$UVC_GS/streaming/class/fs/h
[ -e ${F}/$UVC_GS/streaming/class/hs/h ] || ln -s ${F}/$UVC_GS/streaming/header/h ${F}/$UVC_GS/streaming/class/hs/h
[ -e ${F}/$UVC_GS/streaming/class/ss/h ] || ln -s ${F}/$UVC_GS/streaming/header/h ${F}/$UVC_GS/streaming/class/ss/h

[ -e $C/f1 ] || ln -s ${F}/$UVC_GS $C/f1
log F1=$(readlink $C/f1)
log CTRL=$(ls ${F}/$UVC_GS/control/class)
log STRM=$(ls ${F}/$UVC_GS/streaming/class)
log HDR=$(ls ${F}/$UVC_GS/streaming/header/h)
log MP=$(cat ${F}/$UVC_GS/streaming_maxpacket)
log MAX_SPEED=$(cat $G/max_speed 2>/dev/null)

if [ -f /sys/kernel/debug/dynamic_debug/control ]; then
	echo 'file f_uvc.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'func uvc_function_bind +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'func dwc3_gadget_start +p' > /sys/kernel/debug/dynamic_debug/control
fi
dmesg -c >/tmp/dmesg.pre 2>/dev/null || true

log WRITE_UDC
echo 21500000.usb > $G/UDC
log BIND_RC=$?
log UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
log VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
log ---DMESG---
dmesg | tail -40 | tee -a $LOG

if [ ! -d /sys/class/udc/21500000.usb/device/gadget.0/video4linux ]; then
	log RETRY_1024
	echo none > $G/UDC 2>/dev/null || true
	echo > $G/UDC 2>/dev/null || true
	echo 1024 > ${F}/$UVC_GS/streaming_maxpacket
	dmesg -c >/tmp/dmesg.1024 2>/dev/null || true
	echo 21500000.usb > $G/UDC
	log BIND2_RC=$?
	log UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
	log VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
	dmesg | tail -25 | tee -a $LOG
fi

log WLAN=$(ip -4 addr show wlan0 | grep inet)
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	log UVC_OK
	exit 0
fi
log UVC_FAIL
exit 2
