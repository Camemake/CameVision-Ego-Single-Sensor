#!/bin/sh
ps | grep -E '[s]ingle_imu|[s]ingle_live' || true
echo '=== 8083 ==='
wget -q -O - http://127.0.0.1:8083/ 2>/dev/null | head -c 400
echo
echo '=== 8081/imu ==='
wget -q -O - http://127.0.0.1:8081/imu 2>/dev/null | head -c 400
echo
echo IMU_CHECK
