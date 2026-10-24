#!/bin/sh
G=/sys/kernel/config/usb_gadget/rockchip
U=$G/functions/uvc.gs1
printf 'Camemake' > $G/strings/0x409/product
printf 'Camemake' > $G/strings/0x409/manufacturer
printf 'Camemake' > $U/device_name
printf 'Camemake' > $U/function_name
echo PROD=$(od -An -tx1 $G/strings/0x409/product)
echo DNAME=$(od -An -tx1 $U/device_name)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo ID=$(cat $G/idProduct)
tail -8 /userdata/cv-uvc-bridge.log
