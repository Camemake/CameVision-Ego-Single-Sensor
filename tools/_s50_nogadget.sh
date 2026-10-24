#!/bin/sh
# CV_NO_GADGET — telnet only. Do not bind ADB/UVC/RNDIS.
busybox telnetd -l /bin/sh -p 2323 2>/dev/null || true
ifconfig lo up 2>/dev/null || true
# If a previous gadget is still bound, drop it.
if [ -e /sys/kernel/config/usb_gadget/rockchip/UDC ]; then
	echo none > /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null || true
fi
exit 0
