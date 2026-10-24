G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
# Clear leftover configured by bouncing dwc3, then ADB-only bind (proven).
echo none > $G/UDC 2>/dev/null || true
rm -f $C/f1 $C/f3
# f2 should stay ffs.adb
echo F2=$(readlink $C/f2)
echo 0x0006 > $G/idProduct
echo 0x00 > $G/bDeviceClass
echo 0x00 > $G/bDeviceSubClass
echo 0x00 > $G/bDeviceProtocol
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
sleep 1
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
sleep 1
echo AFTER_DWC STATE=$(cat /sys/class/udc/21500000.usb/state 2>/dev/null) UDC=$(ls /sys/class/udc 2>/dev/null)
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ---usb_config---
head -60 /oem/usr/bin/usb_config.sh
echo ---grep-uvc---
grep -n 'uvc\|UDC\|adb\|wlan\|wifi\|gadget' /oem/usr/bin/usb_config.sh | head -40
echo ---rkuvc---
ls /usr/share/rkuvc.ini /oem/usr/share/rkuvc.ini /tmp/rkuvc.ini 2>/dev/null
echo ---mpi---
ls -l /oem/usr/bin/rk_mpi_uvc /usr/bin/rk_mpi_uvc 2>/dev/null
dmesg | tail -8
