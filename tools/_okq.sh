G=/sys/kernel/config/usb_gadget/rockchip
echo ID=$(cat $G/idProduct)
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo PROD=$(cat $G/strings/0x409/product)
echo F1=$(readlink $G/configs/b.1/f1)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/
ps | grep camevision-uvc-bridge | grep -v grep
echo ---LOG---
cat /userdata/cv-uvc-bridge.log
echo ---CFG---
cat /tmp/.usb_config
