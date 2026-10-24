G=/sys/kernel/config/usb_gadget/rockchip
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) ID=$(cat $G/idProduct)
# Rebind ADB if needed
if [ -z "$(cat $G/UDC)" ]; then
	echo 21500000.usb > $G/UDC
	echo REBIND=$?
fi
for w in connect disconnect 1 0; do
	echo TRY $w
	echo $w > /sys/class/udc/21500000.usb/soft_connect 2>/tmp/sc.err
	echo RC=$? ERR=$(cat /tmp/sc.err)
	sleep 1
	echo STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed) UDC=$(cat $G/UDC)
	if [ "$(cat /sys/class/udc/21500000.usb/state)" = configured ]; then
		echo GOT_CONFIGURED
		break
	fi
done
dmesg | tail -6
echo LIVE=$(ls -l /tmp/camevision-live.jpg | awk '{print $5,$6,$7,$8}')
