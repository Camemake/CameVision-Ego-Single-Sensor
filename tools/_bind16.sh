# UVC-only Camemake HS. No SuperSpeed class. No ADB in this gadget.
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
printf '%s\n' 'usb_adb_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
touch /userdata/camevision-am.on
for p in $(ps | grep -E 'rk_mpi_uvc|uvc.hold|camevision-uvc-bridge' | grep -v grep | awk '{print $1}'); do
	kill -9 $p 2>/dev/null || true
done
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
echo BRIDGE_PRE $!
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
printf '0x0016' > $G/idProduct
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo 500 > $C/MaxPower
echo uvc > $C/strings/0x409/configuration
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
echo 1 > $U/streaming/mjpeg/m/bDefaultFrameIndex 2>/dev/null || true
mkdir -p $U/streaming/header/h
[ -e $U/streaming/header/h/m ] || ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
ln -s $U $C/f1
printf '21500000.usb' > $G/UDC
echo BIND16 ID=$(cat $G/idProduct) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
cat /userdata/cv-uvc-bridge.log
