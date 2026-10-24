G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) ID=$(cat $G/idProduct)
# Destroy and recreate a clean UVC function while ADB owns the UDC.
destroy_uvc() {
	_u=$1
	[ -d "$_u" ] || return 0
	rm -f $_u/streaming/class/fs/h $_u/streaming/class/hs/h $_u/streaming/class/ss/h
	rm -f $_u/streaming/header/h/m $_u/streaming/header/h/u $_u/streaming/header/h/f1 $_u/streaming/header/h/f2
	rmdir $_u/streaming/header/h 2>/dev/null || true
	rm -rf $_u/streaming/mjpeg/m/* $_u/streaming/mjpeg/m 2>/dev/null
	rmdir $_u/streaming/mjpeg/m 2>/dev/null || true
	rmdir $_u/streaming/mjpeg 2>/dev/null || true
	rm -f $_u/control/class/fs/h $_u/control/class/ss/h $_u/control/class/hs/h
	rmdir $_u/control/header/h 2>/dev/null || true
	rmdir $_u 2>/dev/null || true
}
rm -f $C/f1
destroy_uvc $U
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket
echo 2 > $U/uvc_num_request 2>/dev/null || true
echo 0 > $U/streaming_bulk 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h
ln -s $U/control/header/h $U/control/class/ss/h
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth
echo 1600 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1400*1600*16*5)) > $_d/dwMinBitRate
echo $((1400*1600*16*30)) > $_d/dwMaxBitRate
echo $((1400*1600*2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n666666\n1000000\n2000000\n' > $_d/dwFrameInterval
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h
ln -s $U/streaming/header/h $U/streaming/class/hs/h
rm -f $U/streaming/class/ss/h
echo RECREATED w=$(cat $_d/wWidth) h=$(cat $_d/wHeight)
# Keep FunctionFS + adbd alive.
mkdir -p /dev/usb-ffs/adb
mount | grep -q usb-ffs/adb || mount -o uid=2000,gid=2000 -t functionfs adb /dev/usb-ffs/adb
pidof adbd >/dev/null || start-stop-daemon --start --quiet --background --exec /usr/bin/adbd
echo FFS=$(mount | grep usb-ffs/adb)
echo ADBD=$(pidof adbd)
# Dirty empty, keep configured; FFS stays up.
echo disconnect > /sys/class/udc/21500000.usb/soft_connect
ln -s $U $C/f1
[ -e $C/f2 ] || ln -s $G/functions/ffs.adb $C/f2
printf '0x0019' > $G/idProduct
printf '0' > $G/bDeviceClass
printf '0' > $G/bDeviceSubClass
printf '0' > $G/bDeviceProtocol
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo uvc_adb > $C/strings/0x409/configuration
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo F1=$(readlink $C/f1) F2=$(readlink $C/f2)
echo VIDEO
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
	touch /userdata/camevision-am.on
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo BRIDGE $!
	sleep 1
	tail -20 /userdata/cv-uvc-bridge.log
fi
