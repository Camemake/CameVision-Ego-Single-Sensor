G=/sys/kernel/config/usb_gadget/rockchip
echo PRE UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
printf '21500000.usb' > $G/UDC
echo RC $?
echo POST UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo FN
cat $G/functions/uvc.gs6/function_name 2>/dev/null
cat $G/functions/uvc.gs6/device_name 2>/dev/null
echo Camemake > $G/functions/uvc.gs6/function_name
echo Camemake > $G/functions/uvc.gs6/device_name
wget -q -O /userdata/camevision-uvc-bridge.py http://192.168.1.44:18765/b.py
sed -i 's/\r$//' /userdata/camevision-uvc-bridge.py
touch /userdata/camevision-am.on
: > /userdata/cv-uvc-bridge.log
setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
sleep 1
ps | grep camevision-uvc-bridge | grep -v grep
cat /userdata/cv-uvc-bridge.log
dmesg | tail -5
