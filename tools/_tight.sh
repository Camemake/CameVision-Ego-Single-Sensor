G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) ID=$(cat $G/idProduct)
echo UVC
ls $U/streaming/mjpeg/m/ $U/control/class/fs $U/streaming/class/fs $U/streaming/class/hs 2>/dev/null
echo FFS=$(mount | grep usb-ffs/adb)
echo ADBD=$(pidof adbd)
# Tight dirty-empty then composite bind. No extra commands between empty/ln/UDC.
printf '' > $G/UDC
ln -s $U $C/f1
printf '0x0019' > $G/idProduct
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo F1=$(readlink $C/f1) F2=$(readlink $C/f2)
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
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
