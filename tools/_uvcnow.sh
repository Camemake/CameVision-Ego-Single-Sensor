G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo Camemake > $U/device_name 2>/dev/null || true
echo Camemake > $U/function_name 2>/dev/null || true
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
[ -e $U/control/class/fs/h ] || ln -s $U/control/header/h $U/control/class/fs/h
[ -e $U/control/class/ss/h ] || ln -s $U/control/header/h $U/control/class/ss/h
[ -e $U/streaming/class/fs/h ] || ln -s $U/streaming/header/h $U/streaming/class/fs/h
[ -e $U/streaming/class/hs/h ] || ln -s $U/streaming/header/h $U/streaming/class/hs/h
rm -f $U/streaming/class/ss/h
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo TRY_LIVE_ADD
ln -s $U $C/f1
echo LN_RC=$?
echo F1=$(readlink $C/f1)
if [ -e $C/f1 ]; then
	printf '0x0019' > $G/idProduct
	echo LIVE_ID=$(cat $G/idProduct)
	ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
fi
if [ ! -d /sys/class/udc/21500000.usb/device/gadget.0/video4linux ]; then
	echo DIRTY
	echo disconnect > /sys/class/udc/21500000.usb/soft_connect
	rm -f $C/f1
	ln -s $U $C/f1
	printf '0x0019' > $G/idProduct
	echo uvc_adb > $C/strings/0x409/configuration
	printf '21500000.usb' > $G/UDC
	echo BIND_RC=$?
fi
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo VIDEO
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
	touch /userdata/camevision-am.on
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo BRIDGE $!
	sleep 1
	tail -20 /userdata/cv-uvc-bridge.log
fi
dmesg | tail -10
