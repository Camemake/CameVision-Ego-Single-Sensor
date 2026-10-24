G=/sys/kernel/config/usb_gadget/rockchip
echo UDC_NOW
cat $G/UDC
echo STATE
cat /sys/class/udc/21500000.usb/state
echo ID
cat $G/idProduct
echo F1
readlink $G/configs/b.1/f1
printf none > $G/UDC
echo AFTER_NONE_RC $?
cat $G/UDC
echo STATE2
cat /sys/class/udc/21500000.usb/state
# official stop only unbinds
/etc/init.d/S50usbdevice stop
echo AFTER_STOP
cat $G/UDC
echo STATE3
cat /sys/class/udc/21500000.usb/state
ls $G/configs/b.1/
ps | grep camevision-uvc-bridge | grep -v grep
cat /userdata/cv-uvc-bridge.log
