#!/bin/sh
cd /userdata
wget -q -O camevision_ble.py http://192.168.1.44:18765/camevision_ble.py
wget -q -O camevision-ble.sh http://192.168.1.44:18765/camevision-ble.sh
sed -i 's/\r$//' camevision_ble.py camevision-ble.sh
chmod 755 camevision-ble.sh
for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
killall bluetoothctl 2>/dev/null || true
sleep 1
setsid /bin/sh /userdata/camevision-ble.sh </dev/null >/userdata/ble-adv.log 2>&1 &
echo $! >/tmp/camevision-ble.pid
sleep 2
export PYTHONPATH=/userdata/pylib
setsid /usr/bin/python3 /userdata/camevision_agent.py </dev/null >>/userdata/camevision-agent.log 2>&1 &
echo $! >/tmp/camevision-agent.pid
sleep 2
echo '=== procs ==='
ps | grep -E '[c]amevision_agent|[c]amevision-ble.sh|[b]luetoothctl' || true
echo '=== agent ==='
tail -6 /userdata/camevision-agent.log
echo '=== adv ==='
tail -12 /userdata/ble-adv.log
echo '=== wlan ==='
ip -4 addr show wlan0 | grep inet
echo BLE_FIX
