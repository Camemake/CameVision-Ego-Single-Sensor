#!/bin/sh
# Bind Camemake UVC as the first gadget, after UDC and Wi-Fi are up.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin:/oem/usr/bin:$PATH
LOG=/userdata/cv-uvc-first.log
log() { echo "$(cat /proc/uptime) $*" >> "$LOG"; }

i=0
while [ $i -lt 40 ]; do
	if [ -e /sys/class/udc/21500000.usb ]; then
		break
	fi
	i=$((i + 1))
	sleep 1
done
if [ ! -e /sys/class/udc/21500000.usb ]; then
	log NO_UDC
	exit 2
fi

i=0
while [ $i -lt 30 ]; do
	if ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
		break
	fi
	i=$((i + 1))
	sleep 1
done
log "wlan=$(ip -4 addr show wlan0 | grep inet)"

mount -t configfs none /sys/kernel/config 2>/dev/null || true
G=/sys/kernel/config/usb_gadget/rockchip
if [ -d "$G" ]; then
	if [ -n "$(cat $G/UDC 2>/dev/null)" ]; then
		log ALREADY_BOUND
		exit 0
	fi
fi

C=$G/configs/b.1
U=$G/functions/uvc.gs1
mkdir -p $G/strings/0x409
mkdir -p $C/strings/0x409
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
echo 500 > $C/MaxPower
echo uvc > $C/strings/0x409/configuration
mkdir -p $U
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 0 > $U/streaming_bulk 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h 2>/dev/null || true
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth
echo 1600 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1400 * 1600 * 16 * 5)) > $_d/dwMinBitRate
echo $((1400 * 1600 * 16 * 30)) > $_d/dwMaxBitRate
echo $((1400 * 1600 * 2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n666666\n1000000\n2000000\n' > $_d/dwFrameInterval
echo 1 > $U/streaming/mjpeg/m/bDefaultFrameIndex 2>/dev/null || true
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
rm -f $U/streaming/class/ss/h
ln -s $U $C/f1
touch /userdata/camevision-am.on
: > /userdata/cv-uvc-bridge.log
if [ -s /userdata/camevision-uvc-bridge.py ]; then
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	log BRIDGE $!
fi
printf '21500000.usb' > $G/UDC
log BIND_RC $? ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ >> "$LOG" 2>&1
dmesg | tail -6 >> "$LOG"
