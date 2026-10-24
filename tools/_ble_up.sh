#!/bin/sh
# Bring BLE up without power-cycling the combo Wi-Fi chip.
cd /userdata
HOST=http://192.168.1.44:18767
wget -q -O camevision_dbus.py "$HOST/camevision_dbus.py"
wget -q -O camevision_ble.py "$HOST/camevision_ble.py"
wget -q -O camevision_agent.py "$HOST/camevision_agent.py"
wget -q -O camevision-ble.sh "$HOST/camevision-ble.sh"
wget -q -O camevision-wifi.sh "$HOST/camevision-wifi.sh"
sed -i 's/\r$//' camevision_dbus.py camevision_ble.py camevision_agent.py camevision-ble.sh camevision-wifi.sh
chmod 755 camevision-ble.sh camevision-wifi.sh

for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
for p in $(ps | grep '[b]luetoothctl' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
sleep 1

# Reload BT function only. Do not touch wlan0 / swt6621s_wifi.
rmmod skwbt 2>/dev/null || true
sleep 1
if [ -e /proc/skwsdio/bt_service ]; then
	printf 'start\n' > /proc/skwsdio/bt_service
	sleep 2
fi
insmod /userdata/swt6621-rt52/skwbt.ko 2>/dev/null || true
sleep 1

i=0
while [ "$i" -lt 20 ]; do
	hciconfig hci0 up 2>/dev/null || true
	mac=$(hciconfig hci0 2>/dev/null | awk '/BD Address/{print $3}')
	echo "try $i mac=$mac"
	if [ -n "$mac" ] && [ "$mac" != "00:00:00:00:00:00" ]; then
		break
	fi
	i=$((i + 1))
	sleep 1
done

hciconfig hci0 class 0x000620 2>/dev/null || true
hciconfig hci0 piscan 2>/dev/null || true
hciconfig hci0

export PYTHONPATH=/userdata:/userdata/pylib
setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 &
echo $! >/tmp/camevision-agent.pid
sleep 2
setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 &
echo $! >/tmp/camevision-ble.pid
sleep 3
echo ---HCI---
hciconfig hci0
echo ---AGENT---
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo ---LOG---
tail -15 /userdata/camevision-agent.log
echo BLE_UP
