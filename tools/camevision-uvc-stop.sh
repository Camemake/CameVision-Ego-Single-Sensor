#!/bin/sh
# Drop UVC from the composite. Leave ADB. Host may need to unplug/replug.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin:$PATH
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1

if [ -f /tmp/uvc-bridge.pid ]; then
	kill "$(cat /tmp/uvc-bridge.pid)" 2>/dev/null || true
	rm -f /tmp/uvc-bridge.pid
fi
killall camevision-uvc-bridge.py 2>/dev/null || true
rm -f /userdata/uvc-webcam.on

printf 'none' > "$G/UDC" 2>/dev/null || true
sleep 1
rm -f "$C/f2" "$C/f3" "$C/f4" 2>/dev/null
mkdir -p /dev/usb-ffs/adb
mount -o uid=2000,gid=2000 -t functionfs adb /dev/usb-ffs/adb 2>/dev/null || true
mkdir -p "$G/functions/ffs.adb"
[ -e "$C/f1" ] || ln -s "$G/functions/ffs.adb" "$C/f1"
echo 0x0006 > "$G/idProduct"
echo 0 > "$G/bDeviceClass"
echo 0 > "$G/bDeviceSubClass"
echo 0 > "$G/bDeviceProtocol"
echo "CameVision Ego Single Sensor" > "$G/strings/0x409/product" 2>/dev/null || true
echo adb > "$C/strings/0x409/configuration" 2>/dev/null || true
if ! ps | grep -q '[a]dbd'; then
	start-stop-daemon --start --quiet --background --exec /usr/bin/adbd 2>/dev/null || adbd &
fi
sleep 1
echo 21500000.usb > "$G/UDC"
echo "ADB_RESTORED state=$(cat /sys/class/udc/21500000.usb/state) pid=$(cat $G/idProduct)"
