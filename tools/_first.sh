# First gadget bind this boot: HS Camemake UVC-only. UDC has never been used.
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo PRE_UDC
ls /sys/class/udc/
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls -l /sys/class/udc/21500000.usb/gadget 2>/dev/null || echo NO_GADGET
touch /userdata/camevision-am.on
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
echo BRIDGE $!
# Create gadget if S50 stub left none
if [ ! -d $G ]; then
	mkdir -p $G
	mkdir -p $G/strings/0x409
	mkdir -p $C/strings/0x409
fi
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
echo 500 > $C/MaxPower 2>/dev/null || true
echo uvc > $C/strings/0x409/configuration
rm -f $C/f1 $C/f2 $C/f3
rm -f $U/streaming/class/fs/h $U/streaming/class/hs/h $U/streaming/class/ss/h
rm -f $U/control/class/ss/h
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 0 > $U/streaming_bulk 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h 2>/dev/null || true
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
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
ln -s $U $C/f1
printf '21500000.usb' > $G/UDC
echo FIRST_RC $?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
sleep 2
ps | grep camevision-uvc-bridge | grep -v grep
cat /userdata/cv-uvc-bridge.log
dmesg | tail -8
echo UPTIME=$(cat /proc/uptime)
