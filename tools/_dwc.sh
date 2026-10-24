# dwc3 reset then attach Camemake. S50 revert is disabled.
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
printf '%s\n' 'usb_adb_en' 'USB_FORCE_CHANGED' > /tmp/.usb_config
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/unbind
n=0
while [ $n -lt 20 ]; do
	[ ! -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
echo 21500000.usb > /sys/bus/platform/drivers/dwc3/bind
n=0
while [ $n -lt 30 ]; do
	[ -e /sys/class/udc/21500000.usb ] && break
	n=$((n + 1))
	usleep 100000 || sleep 0.1
done
echo DWC3
ls /sys/class/udc/
echo STATE
cat /sys/class/udc/21500000.usb/state
printf '0x0016' > $G/idProduct
printf '239' > $G/bDeviceClass
printf '2' > $G/bDeviceSubClass
printf '1' > $G/bDeviceProtocol
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo uvc > $C/strings/0x409/configuration
rm -f $C/f1 $C/f2 $C/f3
ln -s $U $C/f1
printf '21500000.usb' > $G/UDC
echo BIND ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
tail -8 /userdata/cv-uvc-bridge.log
