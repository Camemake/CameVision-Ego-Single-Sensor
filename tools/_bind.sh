# Camemake UVC+ADB bind. Revert already disabled.
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
touch /userdata/camevision-am.on
printf '%s\n' 'usb_adb_en' 'usb_uvc_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
for p in $(ps | grep -E 'rk_mpi_uvc|uvc.hold|camevision-uvc-bridge' | grep -v grep | awk '{print $1}'); do
	kill -9 $p 2>/dev/null || true
done
printf none > $G/UDC 2>/dev/null || true
n=0
while [ $n -lt 20 ]; do
	[ -z "$(cat $G/UDC)" ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
echo high-speed > $G/max_speed 2>/dev/null || true
printf '0x0200' > $G/bcdUSB
printf '0x2207' > $G/idVendor
printf '0x0019' > $G/idProduct
printf '0' > $G/bDeviceClass
printf '0' > $G/bDeviceSubClass
printf '0' > $G/bDeviceProtocol
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo 500 > $C/MaxPower
echo uvc_adb > $C/strings/0x409/configuration
rm -f $C/f1 $C/f2 $C/f3
rm -f $U/streaming/class/fs/h $U/streaming/class/hs/h $U/streaming/class/ss/h
rm -f $U/streaming/header/h/u $U/streaming/header/h/f $U/streaming/header/h/m
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 0 > $U/streaming_bulk 2>/dev/null || true
mkdir -p $U/control/header/h
[ -e $U/control/class/fs/h ] || ln -s $U/control/header/h $U/control/class/fs/h
[ -e $U/control/class/ss/h ] || ln -s $U/control/header/h $U/control/class/ss/h
set_mjpeg() {
	_d=$U/streaming/mjpeg/m/$1
	mkdir -p $_d
	echo $2 > $_d/wWidth
	echo $3 > $_d/wHeight
	echo 333333 > $_d/dwDefaultFrameInterval
	echo $(($2 * $3 * 16 * 5)) > $_d/dwMinBitRate
	echo $(($2 * $3 * 16 * 30)) > $_d/dwMaxBitRate
	echo $(($2 * $3 * 2)) > $_d/dwMaxVideoFrameBufferSize
	printf '333333\n' > $_d/dwFrameInterval
}
for _d in $U/streaming/mjpeg/m/*; do
	[ -d "$_d" ] || continue
	rmdir $_d 2>/dev/null || true
done
set_mjpeg 1400_1600p 1400 1600
set_mjpeg 1920_1080p 1920 1080
set_mjpeg 1280_720p 1280 720
set_mjpeg 640_480p 640 480
echo 1 > $U/streaming/mjpeg/m/bDefaultFrameIndex 2>/dev/null || true
mkdir -p $U/streaming/header/h
[ -e $U/streaming/header/h/m ] || ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/ss/h 2>/dev/null || true
ln -s $U $C/f1
ln -s $G/functions/ffs.adb $C/f2
: > /userdata/cv-uvc-bridge.log
printf '21500000.usb' > $G/UDC
echo BIND_OK ID=$(cat $G/idProduct) STATE=$(cat /sys/class/udc/21500000.usb/state)
echo F1=$(readlink $C/f1)
echo F2=$(readlink $C/f2)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
cat /userdata/cv-uvc-bridge.log
