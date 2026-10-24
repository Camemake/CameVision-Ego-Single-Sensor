G=/sys/kernel/config/usb_gadget/rockchip
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo F2=$(readlink $G/configs/b.1/f2)
echo F1=$(readlink $G/configs/b.1/f1)
echo 0x0006 > $G/idProduct
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
dmesg | tail -6
