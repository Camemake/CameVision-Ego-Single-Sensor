#!/bin/sh
U=/sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1
echo '=== frames ==='
ls -1 $U/streaming/mjpeg/m
echo '=== intervals ==='
for D in $U/streaming/mjpeg/m/*; do
	[ -d "$D" ] || continue
	echo -n "$(basename $D) "
	echo -n "w=$(cat $D/wWidth) h=$(cat $D/wHeight) def=$(cat $D/dwDefaultFrameInterval) iv="
	tr '\n' ',' < $D/dwFrameInterval
	echo
done
echo -n '12FLAG='; ls /tmp/camevision-uvc-12frames 2>/dev/null || echo no
echo '=== procs ==='
ps | grep -E '[s]ingle_live|[c]amevision-uvc-bridge' || true
echo -n 'STATE='; cat /sys/class/udc/21500000.usb/state
echo -n 'SPEED='; cat /sys/class/udc/21500000.usb/current_speed
echo -n 'WLAN='; ip -4 addr show wlan0 | grep inet
echo '=== ctl ==='
cat /tmp/camevision-uvc-ctl.json 2>/dev/null || echo NO_CTL
wget -q -O - http://127.0.0.1:8081/stat 2>/dev/null || echo NO_STAT
echo
echo '=== live ==='
tail -8 /userdata/single-live.log 2>/dev/null
echo CHECK_DONE
