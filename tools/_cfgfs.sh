mount -t configfs none /sys/kernel/config 2>/dev/null || true
ls /sys/kernel/config/
# If UDC already has a stale gadget pointer, bounce dwc3 now that no gadget exists.
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
n=0
while [ $n -lt 20 ]; do
	[ ! -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
n=0
while [ $n -lt 30 ]; do
	[ -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
sleep 1
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls -l /sys/class/udc/21500000.usb/gadget 2>/dev/null || echo NO_GADGET
G=/sys/kernel/config/usb_gadget/camemake
mkdir -p $G/strings/0x409
mkdir -p $G/configs/b.1/strings/0x409
printf '0x2207' > $G/idVendor
printf '0x0016' > $G/idProduct
printf '0x0200' > $G/bcdUSB
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
echo high-speed > $G/max_speed 2>/dev/null || true
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo 500 > $G/configs/b.1/MaxPower
echo uvc > $G/configs/b.1/strings/0x409/configuration
U=$G/functions/uvc.gs1
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth
echo 1600 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1400 * 1600 * 16 * 5)) > $_d/dwMinBitRate
echo $((1400 * 1600 * 16 * 30)) > $_d/dwMaxBitRate
echo $((1400 * 1600 * 2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n' > $_d/dwFrameInterval
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h
ln -s $U/streaming/header/h $U/streaming/class/hs/h
ln -s $U $G/configs/b.1/f1
printf '21500000.usb' > $G/UDC
echo BIND_RC $?
echo UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -6
tail -8 /userdata/cv-uvc-bridge.log
echo UPTIME=$(cat /proc/uptime)
