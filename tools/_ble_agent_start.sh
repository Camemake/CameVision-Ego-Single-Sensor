#!/bin/sh
cd /userdata
wget -q -O camevision_dbus.py http://192.168.1.44:18765/camevision_dbus.py
wget -q -O camevision_ble.py http://192.168.1.44:18765/camevision_ble.py
wget -q -O camevision_agent.py http://192.168.1.44:18765/camevision_agent.py
wget -q -O camevision-ble.sh http://192.168.1.44:18765/camevision-ble.sh
sed -i 's/\r$//' camevision_dbus.py camevision_ble.py camevision_agent.py camevision-ble.sh
chmod 755 camevision-ble.sh
# Drop the name-only advertiser so GATT can own the LE instance.
for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
killall bluetoothctl 2>/dev/null || true
sleep 1
if ! ps | grep -q '[c]amevision_agent.py'; then
	export PYTHONPATH=/userdata/pylib
	setsid /usr/bin/python3 /userdata/camevision_agent.py </dev/null >>/userdata/camevision-agent.log 2>&1 &
	echo $! >/tmp/camevision-agent.pid
	sleep 2
fi
echo '=== procs ==='
ps | grep -E '[c]amevision_agent|[c]amevision-ble.sh|[b]luetoothd' || true
echo '=== log ==='
tail -30 /userdata/camevision-agent.log 2>/dev/null
echo '=== hci ==='
hciconfig hci0 | head -8
echo '=== wlan ==='
ip -4 addr show wlan0 | grep inet
echo BLE_START
