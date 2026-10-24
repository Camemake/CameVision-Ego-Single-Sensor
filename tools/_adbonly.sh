G=/sys/kernel/config/usb_gadget/rockchip
echo ---who---
head -20 /etc/init.d/S99camevision
echo ===single===
head -20 /etc/init.d/S99camevision-single
echo ===s99uvc===
head -20 /etc/init.d/S99camevision-uvc
echo ===firstlog===
tail -20 /userdata/cv-uvc-first.log
echo ===startlog===
tail -15 /userdata/cv-uvc-start.log
echo ---adb-bind---
# Unlink UVC from this config so first UDC write is ADB-only (proven to work).
rm -f $G/configs/b.1/f1
echo 0x0006 > $G/idProduct
echo 0x00 > $G/bDeviceClass 2>/dev/null || true
echo 0x00 > $G/bDeviceSubClass 2>/dev/null || true
echo 0x00 > $G/bDeviceProtocol 2>/dev/null || true
echo F=$(ls $G/configs/b.1)
echo F2=$(readlink $G/configs/b.1/f2)
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct)
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
dmesg | tail -6
