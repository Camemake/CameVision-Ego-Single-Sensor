G=/sys/kernel/config/usb_gadget/rockchip
U=$G/functions/uvc.gs6
echo ---control---
ls -la $U/control/ $U/control/class/ $U/control/header/ 2>/dev/null
echo ---streaming---
ls -la $U/streaming/class/ $U/streaming/header/h/ $U/streaming/mjpeg/m/ 2>/dev/null
mkdir -p $U/control/class/fs $U/control/class/ss $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h 2>/dev/null || true
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
mkdir -p $U/control/class/hs
ln -s $U/control/header/h $U/control/class/hs/h 2>/dev/null || true
# ensure mjpeg 1400x1600
_d=$U/streaming/mjpeg/m/1600p
if [ ! -d "$_d" ]; then
	_d=$U/streaming/mjpeg/m/1400_1600p
	mkdir -p $_d
	echo 1400 > $_d/wWidth
	echo 1600 > $_d/wHeight
	echo 333333 > $_d/dwDefaultFrameInterval
	printf '333333\n' > $_d/dwFrameInterval
fi
ls $U/streaming/mjpeg/m/
echo Camemake > $U/function_name
echo Camemake > $U/device_name
echo Camemake > $G/strings/0x409/product
echo TRY_BIND
printf '21500000.usb' > $G/UDC
echo RC $?
echo UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -5
