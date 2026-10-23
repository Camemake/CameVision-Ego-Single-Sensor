#!/bin/sh
# Camemake UVC + SD mass-storage. Official ADB S50 stays on disk after bind.
# Do not persist uvc-webcam.on. Do not run usb_config.sh.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
F=$G/functions
C=$G/configs/b.1
UVC_GS=uvc.gs1
LOG=/userdata/cv-rk-uvc.log
: > "$LOG"
log() { echo "$*" | tee -a "$LOG"; }

busybox telnetd -l /bin/sh -p 2323 2>/dev/null || true

exec 9>/tmp/cv-lock-uvc.lock
if command -v flock >/dev/null 2>&1; then
	flock -n 9 || { log LOCKED; exit 0; }
fi

_prep_configfs() {
	if ! grep -q ' /sys/kernel/config ' /proc/mounts; then
		mkdir -p /sys/kernel/config
		mount -t configfs none /sys/kernel/config \
			|| mount -t configfs configfs /sys/kernel/config || true
	fi
	modprobe libcomposite 2>/dev/null || true
	modprobe usb_f_uvc 2>/dev/null || true
	modprobe usb_f_mass_storage 2>/dev/null || true
	mkdir -p "$G" "$F" "$C"
	log CONFIGFS=$(grep configfs /proc/mounts | head -1)
}

_restore_s50() {
	mount -o remount,rw / 2>/dev/null || true
	if [ -f /userdata/cv-s50-bak/S50usbdevice.official ]; then
		rm -f /etc/init.d/S50usbdevice
		cat /userdata/cv-s50-bak/S50usbdevice.official > /etc/init.d/S50usbdevice
		chmod 755 /etc/init.d/S50usbdevice
		log S50_RESTORED
	fi
	if [ -f /userdata/cv-s50-bak/usbdevice.official ]; then
		rm -f /usr/bin/usbdevice
		cat /userdata/cv-s50-bak/usbdevice.official > /usr/bin/usbdevice
		chmod 755 /usr/bin/usbdevice
	fi
}

_prep_configfs

mount -o remount,rw / 2>/dev/null || true
mkdir -p /userdata/cv-s50-bak
if [ -f /etc/init.d/S50usbdevice ] && ! grep -q 'CV_S50_STUB' /etc/init.d/S50usbdevice; then
	cp -a /etc/init.d/S50usbdevice /userdata/cv-s50-bak/S50usbdevice.official
	cp -a /etc/init.d/S50usbdevice /userdata/S50usbdevice
fi
if [ -f /usr/bin/usbdevice ] && ! grep -q 'CV_USBDEVICE_STUB' /usr/bin/usbdevice; then
	cp -a /usr/bin/usbdevice /userdata/cv-s50-bak/usbdevice.official
fi
printf '%s\n' '#!/bin/sh' '# CV_S50_STUB' \
	'busybox telnetd -l /bin/sh -p 2323 2>/dev/null || true' \
	'exit 0' > /etc/init.d/S50usbdevice
chmod 755 /etc/init.d/S50usbdevice
printf '%s\n' '#!/bin/sh' '# CV_USBDEVICE_STUB' 'exit 0' > /usr/bin/usbdevice
chmod 755 /usr/bin/usbdevice
printf 'usb_adb_en\n' > /tmp/.usb_config
log WIFI=$(ip -4 addr show wlan0 | grep inet)

kill $(ps | grep '[c]amevision-ffs-uvc.py' | awk '{print $1}') 2>/dev/null || true
kill $(ps | grep '[c]amevision-uvc-bridge.py' | awk '{print $1}') 2>/dev/null || true
kill $(ps | grep '[c]amevision-usb-sd.sh' | awk '{print $1}') 2>/dev/null || true
killall adbd 2>/dev/null || true

echo none > $G/UDC 2>/dev/null || true
echo > $G/UDC 2>/dev/null || true
sleep 1
umount /dev/usb-ffs/uvc 2>/dev/null || true
umount /dev/usb-ffs/adb 2>/dev/null || true
rm -f $C/f1 $C/f2 $C/f3 $C/f4 $C/ffs.adb $C/ffs.uvc $C/mass_storage.0

_destroy_uvc() {
	_u=$1
	[ -d "$_u" ] || return 0
	rm -f $_u/control/class/fs/h $_u/control/class/ss/h
	rm -f $_u/streaming/class/fs/h $_u/streaming/class/hs/h $_u/streaming/class/ss/h
	rm -f $_u/streaming/header/h/m $_u/streaming/header/h/u
	for _d in $_u/streaming/mjpeg/m/*; do
		[ -d "$_d" ] || continue
		rmdir "$_d" 2>/dev/null || true
	done
	rmdir $_u/streaming/mjpeg/m 2>/dev/null || true
	rmdir $_u/streaming/header/h 2>/dev/null || true
	rmdir $_u/control/header/h 2>/dev/null || true
	rmdir $_u 2>/dev/null || true
}
_destroy_uvc $F/$UVC_GS

mkdir -p $G/strings/0x409
mkdir -p $C/strings/0x409
echo 0x2207 > $G/idVendor
echo 0x0310 > $G/bcdDevice
echo 0x0200 > $G/bcdUSB
# 0/0/0 = composite. 239/2/1 claims the whole device is UVC IAD and
# Windows then drops the camera when mass-storage is also present.
echo 0 > $G/bDeviceClass
echo 0 > $G/bDeviceSubClass
echo 0 > $G/bDeviceProtocol
echo 0x0016 > $G/idProduct
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo 500 > $C/MaxPower
echo uvc+msc > $C/strings/0x409/configuration
echo high-speed > $G/max_speed

mkdir -p $F/$UVC_GS
echo Camemake > $F/$UVC_GS/device_name
echo Camemake > $F/$UVC_GS/function_name
echo 1024 > $F/$UVC_GS/streaming_maxpacket
echo 2 > $F/$UVC_GS/uvc_num_request

CAM_BM=$F/$UVC_GS/control/terminal/camera/default/bmControls
PU_BM=$F/$UVC_GS/control/processing/default/bmControls
# Binary unit bitmaps BEFORE control-header links (attrs go read-only after).
python3 -c "open(r'$CAM_BM','wb').write(bytes([14,0,0]))" || true
python3 -c "open(r'$PU_BM','wb').write(bytes([123,23]))" || true
log CAM_BM=$(od -An -tx1 "$CAM_BM")
log PROC_BM=$(od -An -tx1 "$PU_BM")
mkdir -p $F/$UVC_GS/control/header/h
ln -s $F/$UVC_GS/control/header/h $F/$UVC_GS/control/class/fs/h
ln -s $F/$UVC_GS/control/header/h $F/$UVC_GS/control/class/ss/h
mkdir -p $F/$UVC_GS/streaming/header/h
mkdir -p $F/$UVC_GS/streaming/mjpeg/m

# One interval per frame. This kernel keeps only the last dwFrameInterval write.
_mj1() {
	W=$1; H=$2; IV=$3; FPS=$4; IDX=$5
	D=$F/$UVC_GS/streaming/mjpeg/m/f${IDX}_${W}_${H}_${FPS}
	mkdir -p $D
	echo $W > $D/wWidth
	echo $H > $D/wHeight
	echo $IV > $D/dwDefaultFrameInterval
	echo $((W*H*20)) > $D/dwMinBitRate
	echo $((W*H*60)) > $D/dwMaxBitRate
	echo $((W*H*2)) > $D/dwMaxVideoFrameBufferSize
	printf '%s\n' $IV > $D/dwFrameInterval
	GW=$(cat $D/wWidth)
	GH=$(cat $D/wHeight)
	GIV=$(tr -d '\n' < $D/dwFrameInterval)
	if [ "$GW" != "$W" ] || [ "$GH" != "$H" ] || [ "$GIV" != "$IV" ]; then
		log FRAME_BAD $D want=${W}x${H}@$IV got=${GW}x${GH}@$GIV
		return 1
	fi
	log FRAME_OK $D ${W}x${H}@$FPS
	return 0
}

touch /tmp/camevision-uvc-12frames
BAD=0
if [ -f /userdata/camevision-am.on ]; then
	_mj1 1400 1600 166666 60 01 || BAD=1
	_mj1 1400 1600 333333 30 02 || BAD=1
	_mj1 1400 1600 666666 15 03 || BAD=1
	_mj1 1050 1200 166666 60 04 || BAD=1
	_mj1 1050 1200 333333 30 05 || BAD=1
	_mj1 1050 1200 666666 15 06 || BAD=1
	_mj1 700 800 166666 60 07 || BAD=1
	_mj1 700 800 333333 30 08 || BAD=1
	_mj1 700 800 666666 15 09 || BAD=1
	_mj1 350 400 166666 60 10 || BAD=1
	_mj1 350 400 333333 30 11 || BAD=1
	_mj1 350 400 666666 15 12 || BAD=1
else
	_mj1 1920 1200 166666 60 01 || BAD=1
	_mj1 1920 1200 333333 30 02 || BAD=1
	_mj1 1920 1200 666666 15 03 || BAD=1
	_mj1 1280 800 166666 60 04 || BAD=1
	_mj1 1280 800 333333 30 05 || BAD=1
	_mj1 1280 800 666666 15 06 || BAD=1
	_mj1 960 600 166666 60 07 || BAD=1
	_mj1 960 600 333333 30 08 || BAD=1
	_mj1 960 600 666666 15 09 || BAD=1
	_mj1 640 400 166666 60 10 || BAD=1
	_mj1 640 400 333333 30 11 || BAD=1
	_mj1 640 400 666666 15 12 || BAD=1
fi
echo 1 > $F/$UVC_GS/streaming/mjpeg/m/bDefaultFrameIndex 2>/dev/null || true
ln -s $F/$UVC_GS/streaming/mjpeg/m $F/$UVC_GS/streaming/header/h/m
ln -s $F/$UVC_GS/streaming/header/h $F/$UVC_GS/streaming/class/fs/h
ln -s $F/$UVC_GS/streaming/header/h $F/$UVC_GS/streaming/class/hs/h
ln -s $F/$UVC_GS/streaming/header/h $F/$UVC_GS/streaming/class/ss/h
ln -s $F/$UVC_GS $C/f1

MSC=$F/mass_storage.0
mkdir -p $MSC
echo 1 > $MSC/stall 2>/dev/null || true
echo 1 > $MSC/lun.0/removable 2>/dev/null || true
echo 0 > $MSC/lun.0/cdrom 2>/dev/null || true
echo 0 > $MSC/lun.0/ro 2>/dev/null || true
echo 0 > $MSC/lun.0/nofua 2>/dev/null || true
printf '' > $MSC/lun.0/file 2>/dev/null || echo > $MSC/lun.0/file
ln -s $MSC $C/f2
log MSC=$MSC

echo 21500000.usb > $G/UDC || {
	log UDC_BUSY retry
	sleep 2
	echo none > $G/UDC 2>/dev/null || true
	sleep 1
	echo 21500000.usb > $G/UDC
}
log BIND_RC=$? UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
log VIDEO=$(ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null)
log F01=$(cat $F/$UVC_GS/streaming/mjpeg/m/f01_1400_1600_60/wWidth 2>/dev/null)x$(cat $F/$UVC_GS/streaming/mjpeg/m/f01_1400_1600_60/wHeight 2>/dev/null)

if ! ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
	log UVC_FAIL
	_restore_s50
	exit 2
fi
log UVC_OK BAD=$BAD

touch /userdata/camevision-am.on
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
log BRIDGE=$!
if [ -x /userdata/camevision-usb-sd.sh ]; then
	setsid /bin/sh /userdata/camevision-usb-sd.sh </dev/null >>/userdata/cv-usb-sd.log 2>&1 &
	log USB_SD=$!
fi
sleep 1
tail -8 /userdata/cv-uvc-bridge.log | tee -a "$LOG"

_restore_s50
rm -f /userdata/uvc-webcam.on
mount -o remount,ro / 2>/dev/null || true

log HOLD STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) ID=$(cat $G/idProduct)
log WLAN=$(ip -4 addr show wlan0 | grep inet)
exit 0
