#!/bin/sh
# USB2 High-Speed UVC-only, PID 0x0016. Windows camera name: Camemake.
# Unlink streaming class headers before changing format links. Do not restart S50.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin:/oem/usr/bin:$PATH
export LD_LIBRARY_PATH=/oem/usr/lib:/oem/lib:$LD_LIBRARY_PATH
export rk_mpi_uvc_log_level=2
LOG=/userdata/cv-uvc-gadget.log
log() { echo "$(cat /proc/uptime) $*" >> "$LOG"; }

G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
HOLD=/userdata/camevision-uvc-hold.sh
[ -x "$HOLD" ] || HOLD=/userdata/uvc_hold.sh
IQ=/userdata/iqfiles
[ -d "$IQ" ] || IQ=/oem/usr/share/iqfiles

grep -q USB_FORCE_CHANGED /tmp/.usb_config 2>/dev/null || echo USB_FORCE_CHANGED >> /tmp/.usb_config
cp -f /oem/usr/share/rkuvc.ini /tmp/rkuvc.ini
sed -i 's/enable_aiq = 1/enable_aiq = 0/' /tmp/rkuvc.ini
touch /tmp/uvc_no_timeout /tmp/.uvc_no_timeout
chmod +x "$HOLD" 2>/dev/null || true
for p in $(ps | grep -E 'rk_mpi_uvc|uvc.hold|camevision-uvc-bridge' | grep -v grep | awk '{print $1}'); do
	kill -9 "$p" 2>/dev/null || true
done

printf 'none' > "$G/UDC" 2>/dev/null || true
n=0
while [ $n -lt 20 ]; do
	[ -z "$(cat $G/UDC 2>/dev/null)" ] && break
	n=$((n + 1))
	usleep 100000 2>/dev/null || sleep 0.1
done

if ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
	echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind 2>/dev/null || true
	n=0
	while [ $n -lt 20 ]; do
		[ ! -e /sys/class/udc/21500000.usb ] && break
		n=$((n + 1))
		usleep 100000 2>/dev/null || sleep 0.1
	done
	echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind 2>/dev/null || true
	n=0
	while [ $n -lt 30 ]; do
		[ -e /sys/class/udc/21500000.usb ] && break
		n=$((n + 1))
		usleep 100000 2>/dev/null || sleep 0.1
	done
	log "dwc3 reset"
fi

echo high-speed > "$G/max_speed" 2>/dev/null || true
printf '0x0200' > "$G/bcdUSB"
printf '0x2207' > "$G/idVendor"
printf '0x0016' > "$G/idProduct"
printf '239' > "$G/bDeviceClass"
printf '2' > "$G/bDeviceSubClass"
printf '1' > "$G/bDeviceProtocol"
echo Camemake > "$G/strings/0x409/manufacturer"
echo Camemake > "$G/strings/0x409/product"
echo CV-EGO01-CAM > "$G/strings/0x409/serialnumber"
echo 500 > "$C/MaxPower"
echo uvc > "$C/strings/0x409/configuration"

rm -f "$C/f1" "$C/f2" "$C/f3"
rm -f "$U/streaming/class/fs/h" "$U/streaming/class/hs/h" "$U/streaming/class/ss/h"
rm -f "$U/streaming/header/h/u" "$U/streaming/header/h/f" "$U/streaming/header/h/f1"
mkdir -p "$U"
echo Camemake > "$U/device_name"
echo Camemake > "$U/function_name"
echo 1024 > "$U/streaming_maxpacket" 2>/dev/null || true
echo 0 > "$U/streaming_bulk" 2>/dev/null || true
mkdir -p "$U/control/header/h"
[ -e "$U/control/class/fs/h" ] || ln -s "$U/control/header/h" "$U/control/class/fs/h"
[ -e "$U/control/class/ss/h" ] || ln -s "$U/control/header/h" "$U/control/class/ss/h"

# Default interval must appear in dwFrameInterval or Windows lists the
# device and then refuses a format.
set_mjpeg() {
	_d="$U/streaming/mjpeg/m/$1"
	mkdir -p "$_d"
	echo "$2" > "$_d/wWidth"
	echo "$3" > "$_d/wHeight"
	echo 333333 > "$_d/dwDefaultFrameInterval"
	echo $(($2 * $3 * 16 * 5)) > "$_d/dwMinBitRate"
	echo $(($2 * $3 * 16 * 30)) > "$_d/dwMaxBitRate"
	echo $(($2 * $3 * 2)) > "$_d/dwMaxVideoFrameBufferSize"
	printf '333333\n' > "$_d/dwFrameInterval"
}
for _d in "$U/streaming/mjpeg/m"/*; do
	[ -d "$_d" ] || continue
	rmdir "$_d" 2>/dev/null || true
done
set_mjpeg 1400_1600p 1400 1600
set_mjpeg 1920_1080p 1920 1080
set_mjpeg 1280_720p 1280 720
set_mjpeg 640_480p 640 480
echo 1 > "$U/streaming/mjpeg/m/bDefaultFrameIndex" 2>/dev/null || true

mkdir -p "$U/streaming/header/h"
[ -e "$U/streaming/header/h/m" ] || ln -s "$U/streaming/mjpeg/m" "$U/streaming/header/h/m"
ln -s "$U/streaming/header/h" "$U/streaming/class/fs/h"
ln -s "$U/streaming/header/h" "$U/streaming/class/hs/h"
ln -s "$U/streaming/header/h" "$U/streaming/class/ss/h"
ln -s "$U" "$C/f1"

: > /userdata/cv-uvc-bridge.log
printf '21500000.usb' > "$G/UDC"
log "UVC_OK Camemake UDC=$(cat $G/UDC) fn=$(cat $U/function_name)"
echo "UVC_OK Camemake state=$(cat /sys/class/udc/21500000.usb/state)"
n=0
while [ $n -lt 20 ]; do
	if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
		break
	fi
	n=$((n + 1))
	usleep 100000 2>/dev/null || sleep 0.1
done
BRIDGE=/userdata/camevision-uvc-bridge.py
if [ -f "$BRIDGE" ]; then
	setsid /usr/bin/python3 "$BRIDGE" </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	echo $! >/tmp/camevision-uvc-bridge.pid
else
	rk_mpi_uvc -c /tmp/rkuvc.ini -a "$IQ" -l 2 >>/userdata/cv-rk-mpi-uvc.log 2>&1 &
fi
setsid /bin/sh "$HOLD" </dev/null >/tmp/uvc-hold.log 2>&1 &
sleep 2
echo "UVC_OK after state=$(cat /sys/class/udc/21500000.usb/state) speed=$(cat /sys/class/udc/21500000.usb/current_speed)"
