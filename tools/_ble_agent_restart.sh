#!/bin/sh
cd /userdata
wget -q -O camevision_ble.py http://192.168.1.44:18765/camevision_ble.py
wget -q -O camevision_dbus.py http://192.168.1.44:18765/camevision_dbus.py
sed -i 's/\r$//' camevision_ble.py camevision_dbus.py
for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
sleep 2
export PYTHONPATH=/userdata/pylib
setsid /usr/bin/python3 /userdata/camevision_agent.py </dev/null >>/userdata/camevision-agent.log 2>&1 &
echo $! >/tmp/camevision-agent.pid
sleep 3
bluetoothctl discoverable-timeout 0 >/dev/null 2>&1 || true
bluetoothctl pairable on >/dev/null 2>&1 || true
bluetoothctl discoverable on >/dev/null 2>&1 || true
hciconfig hci0 class 0x000100 2>/dev/null || true
hciconfig hci0 piscan 2>/dev/null || true
ps | grep -E '[c]amevision_agent.py|[b]luetoothd' || true
echo '---LOG---'
tail -12 /userdata/camevision-agent.log
ip -4 addr show wlan0 | grep inet
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Alias|ActiveInstances|Discoverable|Pairable'
echo BLE_RESTART
