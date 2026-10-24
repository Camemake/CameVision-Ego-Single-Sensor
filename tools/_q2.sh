G=/sys/kernel/config/usb_gadget/rockchip
echo ---mjpeg---
ls $G/functions/uvc.gs6/streaming/mjpeg/m/ 2>/dev/null
for d in $G/functions/uvc.gs6/streaming/mjpeg/m/*; do
  [ -d "$d" ] || continue
  echo FRAME $(basename $d) w=$(cat $d/wWidth) h=$(cat $d/wHeight)
done
echo ---header---
ls $G/functions/uvc.gs6/streaming/header/h/ 2>/dev/null
ls $G/functions/uvc.gs6/streaming/class/hs/ 2>/dev/null
echo ---control---
ls $G/functions/uvc.gs6/control/header/h/ 2>/dev/null
echo ---udc-list---
ls /sys/class/udc/
echo ---other-gadgets---
ls /sys/kernel/config/usb_gadget/
for g in /sys/kernel/config/usb_gadget/*; do
  echo GADGET $(basename $g) UDC=$(cat $g/UDC)
done
echo ---s50-uvc---
grep -n 'uvc\|device_name\|function_name\|0019\|0016' /etc/init.d/S50usbdevice | head -40
