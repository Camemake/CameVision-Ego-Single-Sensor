#!/bin/sh
# Make the UDC and configfs actually idle before official UVC bind.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
echo ===BEFORE===
echo UDC=$(cat $G/UDC 2>/dev/null)
echo STATE=$(cat /sys/class/udc/21500000.usb/state 2>/dev/null)
echo F1=$(readlink $C/f1 2>/dev/null)
echo FFS=$(ps | grep '[c]amevision-ffs-uvc' | awk '{print $1}')
echo ADB=$(pidof adbd)
ls -l $C | grep -E 'f[0-9]|ffs'

kill $(ps | grep '[c]amevision-ffs-uvc.py' | awk '{print $1}') 2>/dev/null || true
killall adbd 2>/dev/null || true
sleep 1
umount /dev/usb-ffs/uvc 2>/dev/null || true
umount /dev/usb-ffs/adb 2>/dev/null || true
echo ===AFTER_KILL===
ls /dev/usb-ffs/uvc 2>/dev/null
ls /dev/usb-ffs/adb 2>/dev/null

# Unlink every config function while UDC may still be bound.
rm -f $C/f1 $C/f2 $C/f3 $C/f4 $C/ffs.adb $C/ffs.uvc $C/ffs.ntb
echo ===AFTER_UNLINK===
ls -l $C | grep -E 'f[0-9]|ffs' || echo NO_LINKS

echo none > $G/UDC
echo ===AFTER_NONE===
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo WRITE_EMPTY
# mainline unbind is empty string
echo > $G/UDC
echo UDC2=$(cat $G/UDC)
echo STATE2=$(cat /sys/class/udc/21500000.usb/state)

# Official RkLunch: reset dwc3 so leftover configured is gone.
echo DWC3_UNBIND
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
sleep 2
echo UDC_CLASS=$(ls /sys/class/udc 2>/dev/null)
echo DWC3_BIND
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
sleep 2
echo ===AFTER_DWC===
echo UDC_CLASS=$(ls /sys/class/udc)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo SPEED_MAX=$(cat /sys/class/udc/21500000.usb/maximum_speed)
echo G_UDC=$(cat $G/UDC 2>/dev/null)
echo LINKS=$(ls $C 2>/dev/null)
echo WLAN=$(ip -4 addr show wlan0 | grep inet)

# Destroy leftover UVC/FFS functions now that UDC is idle.
destroy_uvc() {
	_u=$1
	[ -d "$_u" ] || return 0
	rm -f $_u/control/class/fs/h $_u/control/class/hs/h $_u/control/class/ss/h
	rm -f $_u/streaming/class/fs/h $_u/streaming/class/hs/h $_u/streaming/class/ss/h
	rm -f $_u/streaming/header/h/m $_u/streaming/header/h/u $_u/streaming/header/h/f $_u/streaming/header/h/f1 $_u/streaming/header/h/f2
	rmdir $_u/streaming/header/h 2>/dev/null || true
	rmdir $_u/control/header/h 2>/dev/null || true
	rmdir $_u 2>/dev/null || true
	echo DESTROY_$_u=$(test -d $_u && echo STILL || echo GONE)
}
destroy_uvc $G/functions/uvc.gs1
destroy_uvc $G/functions/uvc.gs6
rmdir $G/functions/ffs.uvc 2>/dev/null || true
rmdir $G/functions/ffs.adb 2>/dev/null || true
echo ===FUNCS===
ls $G/functions

echo UMOUNT_CFG
umount /sys/kernel/config
echo UMOUNT_RC=$?
mount | grep configfs || echo NO_CONFIGFS
mkdir -p /sys/kernel/config
mount -t configfs none /sys/kernel/config
echo ===AFTER_REMOUNT===
ls /sys/kernel/config/usb_gadget 2>/dev/null || echo NO_GADGETS
echo WLAN=$(ip -4 addr show wlan0 | grep inet)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
