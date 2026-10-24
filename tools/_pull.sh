G=/sys/kernel/config/usb_gadget/rockchip
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) ID=$(cat $G/idProduct)
echo OOPS
dmesg | grep -E 'Oops|panic|WARNING|dwc3|Call trace' | tail -20
echo PULL
echo disconnect > /sys/class/udc/21500000.usb/soft_connect
sleep 1
echo AFTER STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) UDC=$(cat $G/UDC)
echo ---usb_config bind---
sed -n '119,320p' /oem/usr/bin/usb_config.sh
echo WLAN
ip -4 addr show wlan0 | head -5
echo UPTIME
cat /proc/uptime
