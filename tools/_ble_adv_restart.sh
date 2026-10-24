#!/bin/sh
cd /userdata
wget -q -O camevision-ble.sh http://192.168.1.44:18765/camevision-ble.sh
sed -i 's/\r$//' camevision-ble.sh
chmod 755 camevision-ble.sh
for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
killall bluetoothctl 2>/dev/null || true
sleep 1
printf '%s\n' 'advertise off' 'advertise off' 'advertise off' 'disconnect' 'quit' | bluetoothctl >/dev/null 2>&1 || true
sleep 1
setsid /bin/sh /userdata/camevision-ble.sh </dev/null >/userdata/ble-adv.log 2>&1 &
echo $! >/tmp/camevision-ble.pid
sleep 3
ps | grep -E '[c]amevision-ble.sh|[c]amevision_agent|[b]luetoothctl' || true
echo '---LOG---'
sed 's/\x1b\[[0-9;]*m//g' /userdata/ble-adv.log | grep -E 'data |Failed|Invalid|error|LocalName|RSI|advertise|ActiveInstances|CameVision' | tail -25
echo ADV_OK
