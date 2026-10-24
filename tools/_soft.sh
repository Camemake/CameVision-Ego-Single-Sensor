echo ---mode---
cat /sys/kernel/debug/usb/21500000.usb/mode; echo
ls /sys/kernel/debug/usb/21500000.usb/
echo ---debug---
for x in /sys/kernel/debug/usb/21500000.usb/*; do
	echo "== $x"
	cat "$x" 2>/dev/null | head -20
	echo
done
echo ---dt---
xxd /sys/firmware/devicetree/base/usb@21500000/dr_mode 2>/dev/null
echo ---soft---
cat /sys/class/udc/21500000.usb/soft_connect; echo
echo disconnect > /sys/class/udc/21500000.usb/soft_connect
sleep 1
echo AFTER_DISC STATE=$(cat /sys/class/udc/21500000.usb/state)
echo connect > /sys/class/udc/21500000.usb/soft_connect
sleep 1
echo AFTER_CONN STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo ---rklunch---
head -80 /usr/bin/RkLunch-UVC_TINY.sh 2>/dev/null || head -80 $(which RkLunch-UVC_TINY.sh)
echo ---rklunch-stop---
head -40 /usr/bin/RkLunch-stop-UVC_TINY.sh 2>/dev/null
echo ---which---
ls -l /usr/bin/RkLunch* /oem/usr/bin/RkLunch* 2>/dev/null
