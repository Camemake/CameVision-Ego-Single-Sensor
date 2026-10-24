#!/bin/sh
echo '=== init ==='
ls /etc/init.d | grep -iE 'blue|bt' || true
ls /usr/lib/systemd/system 2>/dev/null | grep -i blue || true
echo '=== before ==='
ip -4 addr show wlan0 | awk '/inet /{print $2}'
hciconfig hci0 | head -4
for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
killall bluetoothctl 2>/dev/null || true
sleep 1
if [ -x /etc/init.d/S40bluetoothd ]; then
	/etc/init.d/S40bluetoothd restart
elif [ -x /etc/init.d/S40bluetooth ]; then
	/etc/init.d/S40bluetooth restart
elif [ -x /etc/init.d/bluetooth ]; then
	/etc/init.d/bluetooth restart
else
	kill 389 2>/dev/null || killall bluetoothd 2>/dev/null || true
	sleep 1
	setsid /usr/libexec/bluetooth/bluetoothd -n </dev/null >/dev/null 2>&1 &
fi
sleep 2
echo '=== after bt ==='
ps | grep '[b]luetoothd' || true
hciconfig hci0 | head -4
ip -4 addr show wlan0 | awk '/inet /{print $2}'
# One named advert from the agent. Leave adapter Discoverable off so
# BlueZ does not add a second nameless instance.
export PYTHONPATH=/userdata/pylib
setsid /usr/bin/python3 /userdata/camevision_agent.py </dev/null >>/userdata/camevision-agent.log 2>&1 &
sleep 3
bluetoothctl power on >/dev/null 2>&1 || true
bluetoothctl discoverable off >/dev/null 2>&1 || true
bluetoothctl pairable on >/dev/null 2>&1 || true
echo '=== procs ==='
ps | grep -E '[c]amevision_agent.py|[b]luetoothd' || true
echo '=== log ==='
tail -8 /userdata/camevision-agent.log
echo '=== show ==='
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Alias|Powered|Discoverable|ActiveInstances'
echo BT_RESTART
