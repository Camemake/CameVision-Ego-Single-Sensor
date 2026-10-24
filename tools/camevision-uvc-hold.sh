#!/bin/sh
# Keep the Camemake JPEG pump attached so the HS UVC gadget stays live.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin:/oem/usr/bin:$PATH
export LD_LIBRARY_PATH=/oem/usr/lib:/oem/lib:$LD_LIBRARY_PATH
BRIDGE=/userdata/camevision-uvc-bridge.py
IQ=/userdata/iqfiles
[ -d "$IQ" ] || IQ=/oem/usr/share/iqfiles
touch /tmp/uvc_no_timeout
touch /tmp/.uvc_no_timeout
while true; do
	if ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/video* >/dev/null 2>&1; then
		if [ -f "$BRIDGE" ]; then
			if ! ps | grep '[c]amevision-uvc-bridge.py' >/dev/null 2>&1; then
				setsid /usr/bin/python3 "$BRIDGE" </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 &
				echo $! >/tmp/camevision-uvc-bridge.pid
			fi
		elif ! pidof rk_mpi_uvc >/dev/null 2>&1; then
			rk_mpi_uvc -c /tmp/rkuvc.ini -a "$IQ" -l 2 \
				>>/userdata/cv-rk-mpi-uvc.log 2>&1 &
			echo $! >/tmp/rk_mpi_uvc.pid
		fi
	fi
	usleep 200000 2>/dev/null || sleep 1
done
