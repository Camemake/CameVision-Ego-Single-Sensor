# New gadget instance after dwc3 reset so leftover gadget.0 cannot hold the UDC.
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
n=0
while [ $n -lt 25 ]; do
	[ ! -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
echo UNBOUND
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
n=0
while [ $n -lt 40 ]; do
	[ -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
sleep 1
echo REBOUND
ls /sys/class/udc/
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls -l /sys/class/udc/21500000.usb/gadget 2>/dev/null || echo NO_GADGET_SYMLINK
G=/sys/kernel/config/usb_gadget/camemake
rm -rf $G 2>/dev/null || true
mkdir -p $G
printf '0x2207' > $G/idVendor
printf '0x0016' > $G/idProduct
printf '0x0200' > $G/bcdUSB
printf '0x0310' > $G/bcdDevice
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
echo high-speed > $G/max_speed 2>/dev/null || true
mkdir -p $G/strings/0x409
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
C=$G/configs/b.1
mkdir -p $C/strings/0x409
echo 500 > $C/MaxPower
echo uvc > $C/strings/0x409/configuration
U=$G/functions/uvc.gs1
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 0 > $U/streaming_bulk 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth
echo 1600 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1400 * 1600 * 16 * 5)) > $_d/dwMinBitRate
echo $((1400 * 1600 * 16 * 30)) > $_d/dwMaxBitRate
echo $((1400 * 1600 * 2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n' > $_d/dwFrameInterval
echo 1 > $U/streaming/mjpeg/m/bDefaultFrameIndex 2>/dev/null || true
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m
ln -s $U/streaming/header/h $U/streaming/class/fs/h
ln -s $U/streaming/header/h $U/streaming/class/hs/h
ln -s $U $C/f1
printf '21500000.usb' > $G/UDC
echo FRESH_RC $?
echo UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
tail -5 /userdata/cv-uvc-bridge.log
