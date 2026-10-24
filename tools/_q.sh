q
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo LIVE
ls -l /tmp/camevision-live.jpg
