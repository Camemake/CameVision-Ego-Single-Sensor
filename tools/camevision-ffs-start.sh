#!/bin/sh
# Bind Camemake UVC via FunctionFS (no f_uvc).
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
mount -o remount,rw / 2>/dev/null || true
if ! grep -q CV_USBDEVICE_STUB /usr/bin/usbdevice; then
	cp -a /usr/bin/usbdevice /userdata/cv-s50-bak/usbdevice.official
	printf '%s\n' '#!/bin/sh' '# CV_USBDEVICE_STUB' 'exit 0' > /usr/bin/usbdevice
	chmod 755 /usr/bin/usbdevice
fi
grep -q USB_FORCE_CHANGED /tmp/.usb_config 2>/dev/null || echo USB_FORCE_CHANGED >> /tmp/.usb_config
mkdir -p $G/functions/ffs.uvc
mkdir -p /dev/usb-ffs/uvc
echo none > $G/UDC 2>/dev/null || true
kill $(ps | grep '[c]amevision-ffs-uvc.py' | awk '{print $1}') 2>/dev/null || true
sleep 1
umount /dev/usb-ffs/uvc 2>/dev/null || true
mount -o uid=0,gid=0 -t functionfs uvc /dev/usb-ffs/uvc
echo MOUNT
mount | grep ffs
ls -l /dev/usb-ffs/uvc
ls $G/functions/ffs.uvc 2>/dev/null | head
: > /userdata/cv-ffs-uvc.log
setsid /usr/bin/python3 /userdata/camevision-ffs-uvc.py </dev/null >>/userdata/cv-ffs-uvc.log 2>&1 &
echo FFS_PY $!
i=0
while [ $i -lt 20 ]; do
	grep -q DESCS_OK /userdata/cv-ffs-uvc.log && break
	i=$((i + 1))
	sleep 0.2
done
echo ---ffs log---
cat /userdata/cv-ffs-uvc.log
if ! grep -q DESCS_OK /userdata/cv-ffs-uvc.log; then
	echo NO_DESCS
	exit 1
fi
echo none > $G/UDC
rm -f $C/f1 $C/f2 $C/f3
ln -s $G/functions/ffs.uvc $C/f1
echo 0x0016 > $G/idProduct
echo 239 > $G/bDeviceClass
echo 2 > $G/bDeviceSubClass
echo 1 > $G/bDeviceProtocol
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo uvc > $C/strings/0x409/configuration
echo high-speed > $G/max_speed 2>/dev/null || true
echo 0x0200 > $G/bcdUSB
echo 21500000.usb > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo F1=$(readlink $C/f1)
dmesg | tail -8
cat /userdata/cv-ffs-uvc.log
