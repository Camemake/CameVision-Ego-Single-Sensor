wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
wc -c /userdata/camevision-uvc-bridge.py
head -c 20 /userdata/camevision-uvc-bridge.py
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
cat /userdata/cv-uvc-bridge.log
echo STILL_ID
cat /sys/kernel/config/usb_gadget/rockchip/idProduct
echo STILL_STATE
cat /sys/class/udc/21500000.usb/state
echo STILL_PROD
cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product
echo STILL_FN
cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1/function_name
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/
