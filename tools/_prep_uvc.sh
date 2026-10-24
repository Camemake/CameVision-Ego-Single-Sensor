mount -o remount,rw / || true
# Stop udev from rebuilding ADB when we unbind.
if ! grep -q CV_USBDEVICE_STUB /usr/bin/usbdevice; then
	cp -a /usr/bin/usbdevice /userdata/cv-s50-bak/usbdevice.official
	printf '%s\n' '#!/bin/sh' '# CV_USBDEVICE_STUB' 'exit 0' > /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
grep -q USB_FORCE_CHANGED /tmp/.usb_config 2>/dev/null || echo USB_FORCE_CHANGED >> /tmp/.usb_config
G=/sys/kernel/config/usb_gadget/rockchip
U=$G/functions/uvc.gs1
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) ID=$(cat $G/idProduct) WLAN=$(ip -4 addr show wlan0 | awk '/inet /{print $2}')
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 2 > $U/uvc_num_request 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h 2>/dev/null || true
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth 2>/dev/null || true
echo 1600 > $_d/wHeight 2>/dev/null || true
echo 333333 > $_d/dwDefaultFrameInterval 2>/dev/null || true
echo $((1400*1600*16*5)) > $_d/dwMinBitRate 2>/dev/null || true
echo $((1400*1600*16*30)) > $_d/dwMaxBitRate 2>/dev/null || true
echo $((1400*1600*2)) > $_d/dwMaxVideoFrameBufferSize 2>/dev/null || true
printf '333333\n666666\n1000000\n2000000\n' > $_d/dwFrameInterval 2>/dev/null || true
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
rm -f $U/streaming/class/ss/h
echo PREPARED w=$(cat $_d/wWidth) h=$(cat $_d/wHeight)
echo USBDEV
head -3 /usr/bin/usbdevice
# start bridge early so it is ready when the node appears
touch /userdata/camevision-am.on
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
echo BRIDGE $!
