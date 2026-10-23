#!/bin/sh
# CameVision Single — start live page + 1 IMU + Wi-Fi/BLE on boot.
# USB starts as official ADB. S99 binds Camemake UVC after the camera is live.
# Do not insmod rockit.
export PATH=/oem/usr/bin:/usr/sbin:/sbin:/usr/bin:/bin
export LD_LIBRARY_PATH=/oem/usr/lib:/oem/lib:$LD_LIBRARY_PATH
export PYTHONPATH=/userdata/pylib${PYTHONPATH:+:$PYTHONPATH}
export TZ=UTC-2

[ -e /dev/rtc0 ] && hwclock -s -f /dev/rtc0 2>/dev/null || true
busybox telnetd -l /bin/sh -p 2323 2>/dev/null || true

BC=/userdata/boot_count
n=0
[ -f "$BC" ] && n=$(cat "$BC" 2>/dev/null || echo 0)
n=$((n + 1))
echo "$n" > "$BC"

[ -e /dev/mpp_service ] || insmod /userdata/kmpp-rt52.ko 2>/dev/null || true

if [ -x /userdata/camevision-hw.sh ]; then
	/userdata/camevision-hw.sh >/userdata/hw-boot.log 2>&1 || true
fi
if [ -x /userdata/camevision-led.sh ]; then
	/userdata/camevision-led.sh >/userdata/led-boot.log 2>&1 || true
fi

if [ -x /userdata/camevision-wifi.sh ]; then
	if ! ip -4 addr show wlan0 2>/dev/null | grep -q 'inet '; then
		if ! ps | grep -q '[c]amevision-wifi'; then
			setsid /bin/sh /userdata/camevision-wifi.sh \
				</dev/null >/userdata/wifi-boot.log 2>&1 &
		fi
	fi
fi

if [ -f /userdata/camevision-am.on ]; then
	if [ -x /userdata/S10mira220 ]; then
		/bin/sh /userdata/S10mira220 >>/userdata/mira220-boot.log 2>&1 || true
	fi
elif [ -x /userdata/camevision-aiq.sh ]; then
	/bin/sh /userdata/camevision-aiq.sh >>/userdata/aiq-boot.log 2>&1 || true
elif ! ps | grep -q '[r]kaiq_3A_server'; then
	setsid /oem/usr/bin/rkaiq_3A_server --silent \
		</dev/null >/userdata/rkaiq.log 2>&1 &
	echo $! >/userdata/rkaiq.pid
fi

if [ -x /userdata/camevision-imu.sh ]; then
	/userdata/camevision-imu.sh >/userdata/imu-boot.log 2>&1 || true
fi

if [ -f /userdata/single_imu_hud.py ] && ! ps | grep -q '[s]ingle_imu_hud'; then
	setsid /usr/bin/python3 /userdata/single_imu_hud.py \
		</dev/null >/tmp/single-imu.log 2>&1 &
	echo $! >/tmp/single-imu.pid
fi

if [ -f /userdata/camevision_agent.py ] && ! ps | grep -q '[c]amevision_agent'; then
	setsid /usr/bin/python3 /userdata/camevision_agent.py \
		</dev/null >/userdata/camevision-agent.log 2>&1 &
	echo $! >/tmp/camevision-agent.pid
fi

i=0
if [ -f /userdata/camevision-am.on ]; then
	WAITDEV=/dev/video1
else
	WAITDEV=/dev/video13
fi
while [ $i -lt 40 ]; do
	if [ -e "$WAITDEV" ]; then
		break
	fi
	i=$((i + 1))
	sleep 1
done

if [ ! -f /userdata/single_live.py ]; then
	echo "missing /userdata/single_live.py"
	exit 0
fi
if ps | grep -q '[s]ingle_live'; then
	exit 0
fi
killall v4l2-ctl 2>/dev/null || true
# SC233 180 is sensor hflip+vflip. MIRA220 AM uses CIF RAW10 — no flip here.
if [ ! -f /userdata/camevision-am.on ]; then
	v4l2-ctl -d /dev/v4l-subdev4 --set-ctrl=horizontal_flip=1 --set-ctrl=vertical_flip=1 2>/dev/null || true
fi
echo "starting single_live $(date 2>/dev/null)"
setsid /usr/bin/python3 /userdata/single_live.py \
	</dev/null >/userdata/single-live.log 2>&1 &
echo $! >/tmp/single-live.pid
echo "pid=$(cat /tmp/single-live.pid)"
exit 0
