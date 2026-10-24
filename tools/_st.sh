echo HI
cat /proc/uptime
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo F1=$(readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1)
echo F2=$(readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo WLAN
ip -4 addr show wlan0 | grep inet
echo ADBD=$(pidof adbd)
