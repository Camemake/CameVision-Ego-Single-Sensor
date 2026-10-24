G=/sys/kernel/config/usb_gadget/rockchip
U=$G/functions/uvc.gs1
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo F1=$(readlink $G/configs/b.1/f1)
echo F2=$(readlink $G/configs/b.1/f2)
echo ID=$(cat $G/idProduct)
echo FRAMES
ls $U/streaming/mjpeg/m/ 2>/dev/null
for d in $U/streaming/mjpeg/m/*; do
	[ -d "$d" ] || continue
	echo $d w=$(cat $d/wWidth) h=$(cat $d/wHeight)
done
echo DISCONNECT
echo disconnect > /sys/class/udc/21500000.usb/soft_connect
sleep 2
echo AFTER_DISC STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
# try connect words
for w in connect connected 1; do
	echo TRY_$w
	echo $w > /sys/class/udc/21500000.usb/soft_connect && echo OK_$w && break
done
sleep 1
echo FINAL STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) UDC=$(cat $G/UDC)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -12
