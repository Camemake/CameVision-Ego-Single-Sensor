echo STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC) ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo F1=$(readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1)
echo ---ffs---
cat /userdata/cv-ffs-uvc.log
echo ---ps---
ps | grep -E 'ffs-uvc|single_live|adbd' | grep -v grep
echo LIVE
ls -l /tmp/camevision-live.jpg
