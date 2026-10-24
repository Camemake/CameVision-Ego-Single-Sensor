G=/sys/kernel/config/usb_gadget/rockchip
U=$G/functions/uvc.gs6
echo ---pre---
echo ID=$(cat $G/idProduct)
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo F1=$(readlink $G/configs/b.1/f1)
echo F2=$(readlink $G/configs/b.1/f2)
echo CTRL=$(ls $U/control/class)
echo STRM=$(ls $U/streaming/class)
echo INITD
ls /etc/init.d/S50* /etc/init.d/S99* 2>/dev/null
echo UD
ls /userdata/*uvc* /userdata/g.sh /userdata/camevision* 2>/dev/null
echo USBDEV
head -2 /usr/bin/usbdevice
# Create HS control (official S50 expects this; this kernel only ships fs+ss).
mkdir $U/control/class/hs 2>/dev/null || true
ln -s $U/control/header/h $U/control/class/hs/h 2>/dev/null || true
# Drop SS control/streaming so HS-only gadget_start is not confused.
rm -f $U/control/class/ss/h
rm -f $U/streaming/class/ss/h
# Keep FS+HS streaming.
[ -e $U/streaming/class/fs/h ] || ln -s $U/streaming/header/h $U/streaming/class/fs/h
[ -e $U/streaming/class/hs/h ] || ln -s $U/streaming/header/h $U/streaming/class/hs/h
echo Camemake > $U/device_name
echo Camemake > $U/function_name
echo Camemake > $G/strings/0x409/product
echo Camemake > $G/strings/0x409/manufacturer
printf '0x0019' > $G/idProduct
echo 0xEF > $G/bDeviceClass 2>/dev/null || true
echo 0x02 > $G/bDeviceSubClass 2>/dev/null || true
echo 0x01 > $G/bDeviceProtocol 2>/dev/null || true
echo ---links---
ls -l $U/control/class/fs $U/control/class/hs $U/control/class/ss 2>/dev/null
ls -l $U/streaming/class/fs $U/streaming/class/hs $U/streaming/class/ss 2>/dev/null
echo TRY_BIND
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct)
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
