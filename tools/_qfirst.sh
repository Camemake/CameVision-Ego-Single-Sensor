echo UPTIME=$(cat /proc/uptime)
echo LOG
cat /userdata/cv-uvc-first.log
echo BRIDGE
tail -20 /userdata/cv-uvc-bridge.log
ps | grep camevision-uvc-bridge | grep -v grep
echo GADGET
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct 2>/dev/null)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null)
echo STATE=$(cat /sys/class/udc/21500000.usb/state 2>/dev/null)
echo PROD=$(cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product 2>/dev/null)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo S50
head -3 /etc/init.d/S50usbdevice
ls /etc/init.d/S50*
