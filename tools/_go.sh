touch /userdata/camevision-am.on
grep -q USB_FORCE_CHANGED /tmp/.usb_config || echo USB_FORCE_CHANGED >> /tmp/.usb_config
wget -q -O /userdata/g.sh http://192.168.1.44:18765/g.sh
wget -q -O /userdata/camevision-uvc-hold.sh http://192.168.1.44:18765/camevision-uvc-hold.sh
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/g.sh /userdata/camevision-uvc-hold.sh /userdata/camevision-uvc-bridge.py
chmod 755 /userdata/g.sh /userdata/camevision-uvc-hold.sh
wc -c /userdata/g.sh /userdata/camevision-uvc-hold.sh /userdata/camevision-uvc-bridge.py
trap '' HUP
sh /userdata/g.sh
echo GO_DONE
cat /tmp/.usb_config
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
ps | grep camevision-uvc-bridge | grep -v grep
tail -15 /userdata/cv-uvc-bridge.log
