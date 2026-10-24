#!/bin/sh
# Bind Camemake UVC without dwc3 reset. Wi-Fi must already be up.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin:/oem/usr/bin:$PATH
if ! ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
	echo NO_WIFI
	exit 2
fi
G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
grep -q USB_FORCE_CHANGED /tmp/.usb_config 2>/dev/null || echo USB_FORCE_CHANGED >> /tmp/.usb_config
for p in $(ps | grep -E 'rk_mpi_uvc|camevision-uvc-bridge' | grep -v grep | awk '{print $1}'); do
	kill -9 "$p" 2>/dev/null || true
done
printf 'none' > "$G/UDC" 2>/dev/null || true
sleep 1
echo high-speed > "$G/max_speed" 2>/dev/null || true
printf '0x0200' > "$G/bcdUSB"
printf '0x2207' > "$G/idVendor"
printf '0x0016' > "$G/idProduct"
printf '239' > "$G/bDeviceClass"
printf '2' > "$G/bDeviceSubClass"
printf '1' > "$G/bDeviceProtocol"
echo Camemake > "$G/strings/0x409/manufacturer"
echo Camemake > "$G/strings/0x409/product"
echo CV-EGO01-CAM > "$G/strings/0x409/serialnumber"
mkdir -p "$U"
echo Camemake > "$U/device_name" 2>/dev/null || true
echo Camemake > "$U/function_name" 2>/dev/null || true
echo 1024 > "$U/streaming_maxpacket" 2>/dev/null || true
rm -f "$C/f1" "$C/f2" "$C/f3"
[ -e "$C/f1" ] || ln -s "$U" "$C/f1"
printf '21500000.usb' > "$G/UDC"
sleep 2
echo SAFE_OK id=$(cat $G/idProduct) fn=$(cat $U/function_name) state=$(cat /sys/class/udc/21500000.usb/state)
if [ -s /userdata/camevision-uvc-bridge.py ]; then
	: > /userdata/cv-uvc-bridge.log
	setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
	setsid /bin/sh /userdata/camevision-uvc-hold.sh </dev/null >/tmp/uvc-hold.log 2>&1 &
	sleep 1
	ps | grep camevision-uvc-bridge | grep -v grep
	tail -8 /userdata/cv-uvc-bridge.log
fi
