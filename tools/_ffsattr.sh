echo ---ffs.uvc---
ls -la /sys/kernel/config/usb_gadget/rockchip/functions/ffs.uvc/
echo ---ep---
ls -l /dev/usb-ffs/uvc/
echo ---dmesg unk---
dmesg | grep -iE 'unknown descriptor|functionfs|ffs' | tail -15
