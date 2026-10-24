mount -o remount,rw / 2>/dev/null || true
cp -a /etc/init.d/S50usbdevice /userdata/cv-s50-bak/S50usbdevice.before-uvc
sed -i 's/CameVision Single/Camemake/' /etc/init.d/S50usbdevice
sed -i 's/"CameMake"/"Camemake"/' /etc/init.d/S50usbdevice
sed -i 's/configure_uvc_resolution_mjpeg 1280 720/configure_uvc_resolution_mjpeg 1400 1600/' /etc/init.d/S50usbdevice
printf '%s\n' 'usb_adb_en' 'usb_uvc_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
touch /userdata/camevision-am.on
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
: > /userdata/cv-uvc-bridge.log
echo PATCH
grep -n 'Camemake\|1400 1600\|usb_uvc_en\|CV_NO_RESTART' /etc/init.d/S50usbdevice
echo BEFORE
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
/etc/init.d/S50usbdevice stop
echo AFTER_STOP
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
/etc/init.d/S50usbdevice start
echo AFTER_START
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo PROD=$(cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product)
ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1/
readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1
readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo Camemake > /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/function_name 2>/dev/null || true
echo Camemake > /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/device_name 2>/dev/null || true
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
tail -15 /userdata/cv-uvc-bridge.log
dmesg | tail -8
echo UPTIME=$(cat /proc/uptime)
