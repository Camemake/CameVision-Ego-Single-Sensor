#!/bin/sh
# Neutralize S50 for this session, then official UVC bind + JPEG pump.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
F=$G/functions
C=$G/configs/b.1
LOG=/userdata/cv-rk-uvc.log
: > $LOG
log() { echo "$*" | tee -a $LOG; }

ip -4 addr show wlan0 | grep -q '192.168.1.72' || { log 'NO_WIFI'; exit 1; }

mount -o remount,rw / 2>/dev/null || true
mkdir -p /userdata/cv-s50-bak
if ! grep -q 'CV_S50_STUB' /etc/init.d/S50usbdevice; then
	cp -a /etc/init.d/S50usbdevice /userdata/cv-s50-bak/S50usbdevice.session
	printf '%s\n' '#!/bin/sh' '# CV_S50_STUB' 'exit 0' > /etc/init.d/S50usbdevice
	chmod 755 /etc/init.d/S50usbdevice
fi
if ! grep -q 'CV_USBDEVICE_STUB' /usr/bin/usbdevice; then
	printf '%s\n' '#!/bin/sh' '# CV_USBDEVICE_STUB' 'exit 0' > /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
printf 'usb_adb_en\n' > /tmp/.usb_config
log S50=$(head -2 /etc/init.d/S50usbdevice)
log USBDEV=$(head -2 /usr/bin/usbdevice)

kill $(ps | grep '[c]amevision-ffs-uvc.py' | awk '{print $1}') 2>/dev/null || true
kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
killall adbd 2>/dev/null || true
echo none > $G/UDC 2>/dev/null || true
echo > $G/UDC 2>/dev/null || true
umount /dev/usb-ffs/uvc 2>/dev/null || true
umount /dev/usb-ffs/adb 2>/dev/null || true
rm -f $C/f1 $C/f2 $C/f3 $C/f4 $C/ffs.adb $C/ffs.uvc

echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
sleep 2
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
sleep 2
log AFTER_DWC STATE=$(cat /sys/class/udc/21500000.usb/state) WLAN=$(ip -4 addr show wlan0 | grep inet)

umount /sys/kernel/config
mount -t configfs none /sys/kernel/config
log GADGETS=$(ls /sys/kernel/config/usb_gadget 2>/dev/null)

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
echo high-speed > $G/max_speed

UVC_GS=uvc.gs1
mkdir -p $F/$UVC_GS
echo Camemake > $F/$UVC_GS/device_name
echo Camemake > $F/$UVC_GS/function_name
echo 1024 > $F/$UVC_GS/streaming_maxpacket
echo 2 > $F/$UVC_GS/uvc_num_request
mkdir -p $F/$UVC_GS/control/header/h
ln -s $F/$UVC_GS/control/header/h $F/$UVC_GS/control/class/fs/h
ln -s $F/$UVC_GS/control/header/h $F/$UVC_GS/control/class/ss/h
mkdir -p $F/$UVC_GS/streaming/header/h

_mj() {
	W=$1; H=$2
	D=$F/$UVC_GS/streaming/mjpeg/m/${W}_${H}p
	mkdir -p $D
	echo $W > $D/wWidth
	echo $H > $D/wHeight
	echo 333333 > $D/dwDefaultFrameInterval
	echo $((W*H*20)) > $D/dwMinBitRate
	echo $((W*H*20)) > $D/dwMaxBitRate
	echo $((W*H*2)) > $D/dwMaxVideoFrameBufferSize
	echo -e "333333\n666666\n1000000\n2000000" > $D/dwFrameInterval
}
# MJPEG 1400x1600 only. NV12 as format 1 makes Windows Camera open
# uncompressed and show a black preview — the pump only feeds JPEG.
mkdir -p $F/$UVC_GS/streaming/mjpeg/m
_mj 1400 1600
echo 1 > $F/$UVC_GS/streaming/mjpeg/m/bDefaultFrameIndex 2>/dev/null || true
ln -s $F/$UVC_GS/streaming/mjpeg/m $F/$UVC_GS/streaming/header/h/m
ln -s $F/$UVC_GS/streaming/header/h $F/$UVC_GS/streaming/class/fs/h
ln -s $F/$UVC_GS/streaming/header/h $F/$UVC_GS/streaming/class/hs/h
ln -s $F/$UVC_GS/streaming/header/h $F/$UVC_GS/streaming/class/ss/h
ln -s $F/$UVC_GS $C/f1

log F1=$(readlink $C/f1) MP=$(cat $F/$UVC_GS/streaming_maxpacket) HDR=$(ls $F/$UVC_GS/streaming/header/h)
dmesg -c >/tmp/dmesg.pre 2>/dev/null || true
echo 21500000.usb > $G/UDC
log BIND_RC=$? UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
log VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
dmesg | tail -15 | tee -a $LOG

if ! ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	log UVC_FAIL
	exit 2
fi
log UVC_OK

# Pump must be subscribed before Windows sends SETUP (no wget here).
touch /userdata/camevision-am.on
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
log BRIDGE=$!
sleep 1
tail -15 /userdata/cv-uvc-bridge.log | tee -a $LOG
log HOLD STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) ID=$(cat $G/idProduct) F1=$(readlink $C/f1)
log WLAN=$(ip -4 addr show wlan0 | grep inet)
exit 0
