#!/bin/sh
cd /userdata
wget -q -O _ble_hold_name.py http://192.168.1.44:18765/_ble_hold_name.py
wget -q -O camevision_dbus.py http://192.168.1.44:18765/camevision_dbus.py
sed -i 's/\r$//' _ble_hold_name.py camevision_dbus.py
for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
killall bluetoothctl 2>/dev/null || true
for p in $(ps | grep '[_]_ble_hold_name.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
sleep 1
printf '%s\n' 'advertise off' 'advertise off' 'discoverable off' 'quit' | bluetoothctl >/dev/null 2>&1 || true
sleep 1
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep ActiveInstances
setsid /usr/bin/python3 /userdata/_ble_hold_name.py </dev/null >/userdata/ble-hold.log 2>&1 &
echo $! >/tmp/camevision-ble-hold.pid
sleep 2
echo '---HOLD---'
cat /userdata/ble-hold.log
printf '%s\n' 'discoverable on' 'quit' | bluetoothctl >/dev/null 2>&1 || true
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Alias|ActiveInstances|Discoverable'
echo HOLD_OK
