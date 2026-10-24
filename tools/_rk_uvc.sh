#!/bin/sh
# Official oem usb_config.sh UVC path, without udev-stop / dwc3 insmod.
# Fresh configfs, exact uvc_device_config, Camemake names, HS-only.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
F=/sys/kernel/config/usb_gadget/rockchip/functions
C=/sys/kernel/config/usb_gadget/rockchip/configs/b.1
LOG=/userdata/cv-rk-uvc.log
: > $LOG
log() { echo "$*" | tee -a $LOG; }

ip -4 addr show wlan0 | grep -q '192.168.1.72' || { log 'NO_WIFI'; exit 1; }

echo none > $G/UDC 2>/dev/null || true
sleep 1
kill $(ps | grep '[c]amevision-ffs-uvc.py' | awk '{print $1}') 2>/dev/null || true
killall adbd 2>/dev/null || true
umount /dev/usb-ffs/uvc 2>/dev/null || true
umount /dev/usb-ffs/adb 2>/dev/null || true

# Official usb_config.sh: tear down configfs and recreate the gadget.
# Do NOT stop udev. Do NOT insmod dwc3 (builtin).
umount /sys/kernel/config 2>/dev/null || true
mkdir -p /sys/kernel/config
mount -t configfs none /sys/kernel/config
log CFG=$(mount | grep configfs)

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
echo 0x1 > $G/os_desc/b_vendor_code
echo MSFT100 > $G/os_desc/qw_sign
echo high-speed > $G/max_speed
log MAX_SPEED=$(cat $G/max_speed)

UVC_GS=uvc.gs1
UVC_NAME=Camemake
mkdir ${F}/$UVC_GS -m 0770
echo $UVC_NAME > ${F}/$UVC_GS/device_name
echo $UVC_NAME > ${F}/$UVC_GS/function_name
echo 3072 > ${F}/$UVC_GS/streaming_maxpacket
echo 2 > ${F}/$UVC_GS/uvc_num_request

mkdir ${F}/$UVC_GS/control/header/h
ln -s ${F}/$UVC_GS/control/header/h ${F}/$UVC_GS/control/class/fs/h
ln -s ${F}/$UVC_GS/control/header/h ${F}/$UVC_GS/control/class/ss/h
mkdir ${F}/$UVC_GS/streaming/header/h

configure_uvc_resolution_nv12() {
	UVC_DISPLAY_W=$1
	UVC_DISPLAY_H=$2
	UVC_DISPLAY_DIR=${F}/$UVC_GS/streaming/uncompressed/u_nv12/${UVC_DISPLAY_W}_${UVC_DISPLAY_H}p
	mkdir ${UVC_DISPLAY_DIR}
	echo $UVC_DISPLAY_W > ${UVC_DISPLAY_DIR}/wWidth
	echo $UVC_DISPLAY_H > ${UVC_DISPLAY_DIR}/wHeight
	echo 333333 > ${UVC_DISPLAY_DIR}/dwDefaultFrameInterval
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*20)) > ${UVC_DISPLAY_DIR}/dwMinBitRate
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*20)) > ${UVC_DISPLAY_DIR}/dwMaxBitRate
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*2)) > ${UVC_DISPLAY_DIR}/dwMaxVideoFrameBufferSize
	echo -e "333333\n666666\n1000000\n2000000" > ${UVC_DISPLAY_DIR}/dwFrameInterval
	echo 12 > ${F}/$UVC_GS/streaming/uncompressed/u_nv12/bBitsPerPixel
	echo -ne \\x4e\\x56\\x31\\x32\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/uncompressed/u_nv12/guidFormat
}
configure_uvc_resolution_mjpeg() {
	UVC_DISPLAY_W=$1
	UVC_DISPLAY_H=$2
	UVC_DISPLAY_DIR=${F}/$UVC_GS/streaming/mjpeg/m/${UVC_DISPLAY_W}_${UVC_DISPLAY_H}p
	mkdir ${UVC_DISPLAY_DIR}
	echo $UVC_DISPLAY_W > ${UVC_DISPLAY_DIR}/wWidth
	echo $UVC_DISPLAY_H > ${UVC_DISPLAY_DIR}/wHeight
	echo 333333 > ${UVC_DISPLAY_DIR}/dwDefaultFrameInterval
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*20)) > ${UVC_DISPLAY_DIR}/dwMinBitRate
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*20)) > ${UVC_DISPLAY_DIR}/dwMaxBitRate
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*2)) > ${UVC_DISPLAY_DIR}/dwMaxVideoFrameBufferSize
	echo -e "333333\n666666\n1000000\n2000000" > ${UVC_DISPLAY_DIR}/dwFrameInterval
	echo -ne \\x4d\\x4a\\x50\\x47\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/mjpeg/m/guidFormat
}
configure_uvc_resolution_h264() {
	UVC_DISPLAY_W=$1
	UVC_DISPLAY_H=$2
	UVC_DISPLAY_DIR=${F}/$UVC_GS/streaming/framebased/f1/${UVC_DISPLAY_W}_${UVC_DISPLAY_H}p
	mkdir ${UVC_DISPLAY_DIR}
	echo $UVC_DISPLAY_W > ${UVC_DISPLAY_DIR}/wWidth
	echo $UVC_DISPLAY_H > ${UVC_DISPLAY_DIR}/wHeight
	echo 333333 > ${UVC_DISPLAY_DIR}/dwDefaultFrameInterval
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*10)) > ${UVC_DISPLAY_DIR}/dwMinBitRate
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*10)) > ${UVC_DISPLAY_DIR}/dwMaxBitRate
	echo -e "333333\n400000\n500000\n666666\n1000000\n2000000" > ${UVC_DISPLAY_DIR}/dwFrameInterval
	echo -ne \\x48\\x32\\x36\\x34\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/framebased/f1/guidFormat
}
configure_uvc_resolution_h265() {
	UVC_DISPLAY_W=$1
	UVC_DISPLAY_H=$2
	UVC_DISPLAY_DIR=${F}/$UVC_GS/streaming/framebased/f2/${UVC_DISPLAY_W}_${UVC_DISPLAY_H}p
	mkdir ${UVC_DISPLAY_DIR}
	echo $UVC_DISPLAY_W > ${UVC_DISPLAY_DIR}/wWidth
	echo $UVC_DISPLAY_H > ${UVC_DISPLAY_DIR}/wHeight
	echo 333333 > ${UVC_DISPLAY_DIR}/dwDefaultFrameInterval
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*10)) > ${UVC_DISPLAY_DIR}/dwMinBitRate
	echo $((UVC_DISPLAY_W*UVC_DISPLAY_H*10)) > ${UVC_DISPLAY_DIR}/dwMaxBitRate
	echo -e "333333\n400000\n500000\n666666" > ${UVC_DISPLAY_DIR}/dwFrameInterval
	echo -ne \\x48\\x32\\x36\\x35\\x00\\x00\\x10\\x00\\x80\\x00\\x00\\xaa\\x00\\x38\\x9b\\x71 > ${F}/$UVC_GS/streaming/framebased/f2/guidFormat
}

mkdir ${F}/$UVC_GS/streaming/uncompressed/u_nv12
configure_uvc_resolution_nv12 1280 720
configure_uvc_resolution_nv12 1920 1080
ln -s ${F}/$UVC_GS/streaming/uncompressed/u_nv12 ${F}/$UVC_GS/streaming/header/h/u

mkdir ${F}/$UVC_GS/streaming/mjpeg/m
configure_uvc_resolution_mjpeg 1024 768
configure_uvc_resolution_mjpeg 1920 1080
configure_uvc_resolution_mjpeg 1400 1600
ln -s ${F}/$UVC_GS/streaming/mjpeg/m ${F}/$UVC_GS/streaming/header/h/m

mkdir ${F}/$UVC_GS/streaming/framebased/f1
configure_uvc_resolution_h264 1280 720
configure_uvc_resolution_h264 1920 1080
ln -s ${F}/$UVC_GS/streaming/framebased/f1 ${F}/$UVC_GS/streaming/header/h/f1

mkdir ${F}/$UVC_GS/streaming/framebased/f2
configure_uvc_resolution_h265 1280 720
configure_uvc_resolution_h265 1920 1080
ln -s ${F}/$UVC_GS/streaming/framebased/f2 ${F}/$UVC_GS/streaming/header/h/f2

ln -s ${F}/$UVC_GS/streaming/header/h ${F}/$UVC_GS/streaming/class/fs/h
ln -s ${F}/$UVC_GS/streaming/header/h ${F}/$UVC_GS/streaming/class/hs/h
ln -s ${F}/$UVC_GS/streaming/header/h ${F}/$UVC_GS/streaming/class/ss/h

ln -s ${F}/$UVC_GS $C/f1
log F1=$(readlink $C/f1)
log CTRL=$(ls ${F}/$UVC_GS/control/class)
log STRM=$(ls ${F}/$UVC_GS/streaming/class)
log HDR=$(ls ${F}/$UVC_GS/streaming/header/h)
log MP=$(cat ${F}/$UVC_GS/streaming_maxpacket)
log UDC_MAX=$(cat /sys/class/udc/21500000.usb/maximum_speed)
log UDC_STATE=$(cat /sys/class/udc/21500000.usb/state)

if [ -f /sys/kernel/debug/dynamic_debug/control ]; then
	echo 'file f_uvc.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'file uvc_configfs.c +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'func uvc_function_bind +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'func dwc3_gadget_start +p' > /sys/kernel/debug/dynamic_debug/control
	echo 'func dwc3_gadget_resize_tx_fifos +p' > /sys/kernel/debug/dynamic_debug/control
fi
dmesg -c >/tmp/dmesg.pre 2>/dev/null || true

echo 21500000.usb > $G/UDC
log BIND1_RC=$?
log UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
log VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
log ---DMESG1---
dmesg | tail -40 | tee -a $LOG

if [ ! -d /sys/class/udc/21500000.usb/device/gadget.0/video4linux ]; then
	log DWC3_RESET
	echo none > $G/UDC 2>/dev/null || true
	sleep 1
	echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
	sleep 2
	echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
	sleep 2
	log AFTER_DWC WLAN=$(ip -4 addr show wlan0 | grep inet)
	log UDC_DEV=$(ls /sys/class/udc)
	dmesg -c >/tmp/dmesg.dwc 2>/dev/null || true
	echo 21500000.usb > $G/UDC
	log BIND2_RC=$?
	log UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
	log VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
	log ---DMESG2---
	dmesg | tail -40 | tee -a $LOG
fi

if [ ! -d /sys/class/udc/21500000.usb/device/gadget.0/video4linux ]; then
	log RETRY_1024
	echo none > $G/UDC 2>/dev/null || true
	echo 1024 > ${F}/$UVC_GS/streaming_maxpacket
	dmesg -c >/tmp/dmesg.1024 2>/dev/null || true
	echo 21500000.usb > $G/UDC
	log BIND3_RC=$?
	log UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
	log VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
	dmesg | tail -25 | tee -a $LOG
fi

log WLAN
ip -4 addr show wlan0 | grep inet | tee -a $LOG
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	log UVC_OK
	exit 0
fi
log UVC_FAIL
exit 2
