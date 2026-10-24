echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo F1=$(readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1)
echo CFG
cat /tmp/.usb_config
echo PS
ps | grep -E 'adbd|usb_config|S50|usbdevice' | grep -v grep
echo S99
ls /etc/init.d/
echo ===s99files===
grep -n 'usb\|adbd\|gadget' /etc/init.d/S99* /etc/init.d/S80* /etc/init.d/S90* /userdata/camevision*.sh /userdata/S99* 2>/dev/null | head -40
echo OEMCFG
head -5 /oem/usr/bin/usb_config.sh
grep -n 'idProduct\|UDC\|usb_adb\|start' /oem/usr/bin/usb_config.sh | head -20
