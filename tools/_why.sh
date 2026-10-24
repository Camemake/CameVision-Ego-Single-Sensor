G=/sys/kernel/config/usb_gadget/rockchip
echo UDC
cat $G/UDC
echo STATE
cat /sys/class/udc/21500000.usb/state
echo F1
ls -l $G/configs/b.1/
echo UVC
ls $G/functions/uvc.gs1/ 2>/dev/null
ls $G/functions/uvc.gs1/streaming/mjpeg/m/ 2>/dev/null
ls $G/functions/uvc.gs1/streaming/header/h/ 2>/dev/null
ls $G/functions/uvc.gs1/streaming/class/hs/ 2>/dev/null
ls $G/functions/uvc.gs1/control/class/fs/ 2>/dev/null
echo DMESG
dmesg | tail -25
