G=/sys/kernel/config/usb_gadget/rockchip
echo ID=$(cat $G/idProduct)
echo UDC=$(cat $G/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo PRODUCT=$(cat $G/strings/0x409/product)
echo FN=$(cat $G/functions/uvc.gs1/function_name)
echo F1=$(readlink $G/configs/b.1/f1)
echo CFG
cat /tmp/.usb_config
echo PS
ps | grep -E 'camevision-uvc-bridge|usbdevice|S50' | grep -v grep
echo LOG
cat /userdata/cv-uvc-bridge.log
echo JPG
ls -l /tmp/camevision-live.jpg
echo AM
ls -l /userdata/camevision-am.on
