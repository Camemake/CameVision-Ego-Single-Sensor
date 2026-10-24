#!/bin/sh
# Build Camemake UVC while ADB is live, then switch UDC with no delay.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin:/oem/usr/bin:$PATH
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1

if ! ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
	echo NO_WIFI
	exit 2
fi

mount -o remount,rw / 2>/dev/null || true
mkdir -p /userdata/cv-s50-bak
for f in /etc/init.d/S50usbdevice.cvbak /etc/init.d/S50usbdevice.cvpreuvc; do
	if [ -e "$f" ]; then
		mv -f "$f" /userdata/cv-s50-bak/
	fi
done
if [ ! -f /usr/bin/usbdevice.cvbak ]; then
	cp -a /usr/bin/usbdevice /usr/bin/usbdevice.cvbak 2>/dev/null || true
fi
printf '%s\n' '#!/bin/sh' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
if [ -f /lib/udev/rules.d/61-usbdevice.rules ]; then
	mv -f /lib/udev/rules.d/61-usbdevice.rules /lib/udev/rules.d/61-usbdevice.rules.cvoff
	udevadm control --reload 2>/dev/null || true
fi
if ! grep -q CV_NO_RESTART /etc/init.d/S50usbdevice; then
	cp -a /etc/init.d/S50usbdevice /userdata/cv-s50-bak/S50usbdevice.live
	sed -i 's/^restart|reload)/restart|reload)\n	exit 0\n	# CV_NO_RESTART/' /etc/init.d/S50usbdevice
fi
if [ -f /userdata/camevision-uvc-stop.sh ]; then
	mv -f /userdata/camevision-uvc-stop.sh /userdata/camevision-uvc-stop.sh.off
fi
printf '%s\n' 'usb_adb_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
touch /userdata/camevision-am.on

wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
for p in $(ps | grep -E 'rk_mpi_uvc|uvc.hold|camevision-uvc-bridge' | grep -v grep | awk '{print $1}'); do
	kill -9 "$p" 2>/dev/null || true
done
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
echo BRIDGE $!

# Prepare unused uvc.gs1 while ADB still owns the UDC.
echo high-speed > "$G/max_speed" 2>/dev/null || true
rm -f "$U/streaming/class/fs/h" "$U/streaming/class/hs/h" "$U/streaming/class/ss/h"
rm -f "$U/streaming/header/h/u" "$U/streaming/header/h/f" "$U/streaming/header/h/m"
rm -f "$U/control/class/ss/h"
mkdir -p "$U"
echo Camemake > "$U/device_name"
echo Camemake > "$U/function_name"
echo 1024 > "$U/streaming_maxpacket" 2>/dev/null || true
echo 0 > "$U/streaming_bulk" 2>/dev/null || true
mkdir -p "$U/control/header/h"
ln -s "$U/control/header/h" "$U/control/class/fs/h" 2>/dev/null || true
ln -s "$U/control/header/h" "$U/control/class/hs/h" 2>/dev/null || true
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
	if [ -d "$_d" ]; then
		rmdir "$_d" 2>/dev/null || true
	fi
done
set_mjpeg 1400_1600p 1400 1600
echo 1 > "$U/streaming/mjpeg/m/bDefaultFrameIndex" 2>/dev/null || true
mkdir -p "$U/streaming/header/h"
ln -s "$U/streaming/mjpeg/m" "$U/streaming/header/h/m" 2>/dev/null || true
ln -s "$U/streaming/header/h" "$U/streaming/class/fs/h" 2>/dev/null || true
ln -s "$U/streaming/header/h" "$U/streaming/class/hs/h" 2>/dev/null || true
rm -f "$U/streaming/class/ss/h"
echo PREPARED

# Switch UDC in one burst. No sleeps.
printf 'none' > "$G/UDC"
rm -f "$C/f1" "$C/f2" "$C/f3"
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
ln -s "$U" "$C/f1"
printf '21500000.usb' > "$G/UDC"
echo FAST_RC $?
echo ID=$(cat "$G/idProduct") UDC=$(cat "$G/UDC") STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
tail -15 /userdata/cv-uvc-bridge.log
dmesg | tail -8
echo UPTIME=$(cat /proc/uptime)
