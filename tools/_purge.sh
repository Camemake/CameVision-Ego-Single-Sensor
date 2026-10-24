G=/sys/kernel/config/usb_gadget/rockchip
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
n=0
while [ $n -lt 25 ]; do
	[ ! -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
umount /dev/usb-ffs/adb 2>/dev/null || true
umount /dev/usb-ffs/ntb 2>/dev/null || true
printf none > $G/UDC 2>/dev/null || true
rm -f $G/configs/b.1/f1 $G/configs/b.1/f2 $G/configs/b.1/f3 $G/os_desc/b.1
echo ---configs---
ls -la $G/configs/b.1/ 2>/dev/null
echo ---functions---
ls $G/functions/ 2>/dev/null
for f in $G/functions/*; do
	echo TRY $f
	rmdir $f 2>/dev/null && echo RMDIR_OK $f || ls $f 2>/dev/null | head
done
# UVC leftovers
for U in $G/functions/uvc.gs1 $G/functions/uvc.gs6; do
	[ -d "$U" ] || continue
	rm -f $U/streaming/class/fs/h $U/streaming/class/hs/h $U/streaming/class/ss/h
	rm -f $U/streaming/header/h/m $U/streaming/header/h/u $U/streaming/header/h/f
	rmdir $U/streaming/header/h 2>/dev/null || true
	for d in $U/streaming/mjpeg/m/* $U/streaming/uncompressed/u/* $U/streaming/framebased/f/*; do
		[ -d "$d" ] && rmdir "$d" 2>/dev/null || true
	done
	rmdir $U/streaming/mjpeg/m $U/streaming/mjpeg 2>/dev/null || true
	rmdir $U/streaming/uncompressed/u $U/streaming/uncompressed 2>/dev/null || true
	rmdir $U/streaming/framebased/f $U/streaming/framebased 2>/dev/null || true
	rm -f $U/control/class/fs/h $U/control/class/ss/h
	rmdir $U/control/header/h 2>/dev/null || true
	rmdir $U 2>/dev/null && echo UVC_GONE $U
done
for f in $G/functions/*; do
	rmdir $f 2>/dev/null && echo FN_GONE $f
done
rmdir $G/configs/b.1/strings/0x409 2>/dev/null || true
rmdir $G/configs/b.1 2>/dev/null || true
rmdir $G/strings/0x409 2>/dev/null || true
rmdir $G 2>/dev/null && echo ROCKCHIP_GONE
echo ---left---
ls -la /sys/kernel/config/usb_gadget/
ls $G 2>/dev/null
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
n=0
while [ $n -lt 40 ]; do
	[ -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
sleep 1
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls -l /sys/class/udc/21500000.usb/gadget 2>/dev/null || echo NO_GADGET_SYMLINK
