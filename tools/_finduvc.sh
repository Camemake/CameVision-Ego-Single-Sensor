find /oem /usr /lib /ko -name '*uvc*' 2>/dev/null | head -40
ls /oem/usr/ko/ 2>/dev/null | head -40
echo ---video names---
for d in /sys/class/video4linux/video*; do
	echo $d $(cat $d/name 2>/dev/null)
done | grep -iE 'uvc|gadget|camemake|dummy' 
echo ---adb---
pidof adbd
echo STATE=$(cat /sys/class/udc/21500000.usb/state) ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct) UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC)
