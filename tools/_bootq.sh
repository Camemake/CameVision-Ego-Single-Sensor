echo UPTIME
cat /proc/uptime
echo CFG
cat /tmp/.usb_config
echo ID
cat /sys/kernel/config/usb_gadget/rockchip/idProduct
echo UDC
cat /sys/kernel/config/usb_gadget/rockchip/UDC
echo STATE
cat /sys/class/udc/21500000.usb/state
echo PROD
cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product
echo F1
ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1/
readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1
readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2
echo V4L
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo DMESG
dmesg | grep -E 'uvc_function|failed to start|UDC core|dwc3 215' | tail -15
echo LIVE
ls -l /tmp/camevision-live.jpg
ps | grep single_live | grep -v grep
