#!/bin/sh
# Restore CameVision GATT after the SD reboot race. Do not kill bluetoothd.
cd /userdata
HOST=http://192.168.1.44:18765
wget -q -O camevision_agent.py "$HOST/camevision_agent.py"
wget -q -O camevision_ble.py "$HOST/camevision_ble.py"
wget -q -O camevision-ble.sh "$HOST/camevision-ble.sh"
sed -i 's/\r$//' camevision_agent.py camevision_ble.py camevision-ble.sh
chmod 755 camevision-ble.sh
hciconfig hci0 class 0x000620 2>/dev/null || true
for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
for p in $(ps | grep '[b]luetoothctl' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
sleep 2
export PYTHONPATH=/userdata/pylib
setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 &
echo $! >/tmp/camevision-agent.pid
setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 &
echo $! >/tmp/camevision-ble.pid
sleep 4
echo RESTARTED
tail -20 /userdata/camevision-agent.log
echo CLASS
bluetoothctl show
echo WIFI
ip -4 addr show wlan0 | grep inet
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo FIX_PAIR
