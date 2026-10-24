echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct)
echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo F1=$(readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1)
echo FFS=$(ps | grep '[c]amevision-ffs-uvc')
echo LIVE
ls -l /tmp/camevision-live.jpg
echo WLAN
ip -4 addr show wlan0 | grep inet
echo UPTIME
cat /proc/uptime
echo KVER
uname -r
echo ---ffs---
ls /dev/usb-ffs/uvc/ 2>/dev/null
tail -10 /userdata/cv-ffs-uvc.log
