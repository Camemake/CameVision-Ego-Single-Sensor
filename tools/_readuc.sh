echo ---tail usb_config---
sed -n '320,520p' /oem/usr/bin/usb_config.sh
echo ---builtin---
grep uvc /lib/modules/$(uname -r)/modules.builtin 2>/dev/null
ls /oem/usr/ko/usb_f_uvc.ko /lib/modules/*/usb_f_uvc.ko 2>/dev/null
echo ---lsmod---
lsmod | grep -E 'uvc|dwc|composite|gadget' 
echo ---gadget0---
ls -la /sys/devices/platform/21500000.usb/gadget.0/ 2>/dev/null | head
echo ---rkuvc ini---
head -80 /oem/usr/share/rkuvc.ini
echo WLAN
ip -4 addr show wlan0 | grep inet
echo ---restore ADB---
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
rm -f $C/f1
mkdir -p /dev/usb-ffs/adb
mount -o uid=2000,gid=2000 -t functionfs adb /dev/usb-ffs/adb 2>/dev/null || true
start-stop-daemon --start --quiet --background --exec /usr/bin/adbd
ln -s $G/functions/ffs.adb $C/f2 2>/dev/null || true
printf '0x0006' > $G/idProduct
printf '0' > $G/bDeviceClass
printf '0' > $G/bDeviceSubClass
printf '0' > $G/bDeviceProtocol
printf '21500000.usb' > $G/UDC
echo ADB_RC=$? STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC)
