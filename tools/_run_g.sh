trap '' HUP
/bin/sh /userdata/g.sh
echo GO_DONE
sleep 3
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo PRODUCT=$(cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product)
readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1
readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/
ps | grep camevision-uvc-bridge | grep -v grep
cat /tmp/.usb_config
tail -20 /userdata/cv-uvc-bridge.log
