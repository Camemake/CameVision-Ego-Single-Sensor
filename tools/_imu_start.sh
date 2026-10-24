#!/bin/sh
cd /userdata
wget -q -O single_imu_hud.py http://192.168.1.44:18765/single_imu_hud.py
sed -i 's/\r$//' single_imu_hud.py
if ! ps | grep -q '[s]ingle_imu_hud'; then
	setsid /usr/bin/python3 /userdata/single_imu_hud.py </dev/null >>/tmp/single-imu.log 2>&1 &
	sleep 1
fi
ps | grep '[s]ingle_imu_hud' || true
echo '=== log ==='
tail -20 /tmp/single-imu.log 2>/dev/null
echo '=== json ==='
wget -q -O - http://127.0.0.1:8083/ 2>/dev/null | head -c 500
echo
echo IMU_START
