U=/sys/class/udc/21500000.usb
echo ---udc---
echo state=$(cat $U/state)
echo speed=$(cat $U/current_speed)
echo max=$(cat $U/maximum_speed)
echo fn=$(cat $U/function)
echo soft=$(cat $U/soft_connect)
ls -l $U/gadget 2>/dev/null
echo ---try adb---
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
rm -f $C/f1 $C/f2
ln -s $G/functions/ffs.adb $C/f1
printf '0x0006' > $G/idProduct
printf '0' > $G/bDeviceClass
echo adb > $C/strings/0x409/configuration
printf '21500000.usb' > $G/UDC
echo ADB_BIND $?
echo UDC=$(cat $G/UDC) STATE=$(cat $U/state)
dmesg | tail -5
