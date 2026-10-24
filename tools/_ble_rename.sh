#!/bin/sh
# Force "CameVision Ego Single" + last 6 MAC hex. Drop every old advertiser.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
if [ -f /tmp/camevision-ble.pid ]; then
	kill "$(cat /tmp/camevision-ble.pid)" 2>/dev/null || true
	rm -f /tmp/camevision-ble.pid
fi
killall bluetoothctl 2>/dev/null || true
sleep 1
bluetoothctl advertise off >/dev/null 2>&1 || true
bluetoothctl power off >/dev/null 2>&1 || true
sleep 1
bluetoothctl power on >/dev/null 2>&1 || true
sleep 1
hciconfig hci0 up 2>/dev/null || true
mac=$(hciconfig hci0 2>/dev/null | awk '/BD Address/{print $3}' | tr -d ':' | tr 'a-f' 'A-F')
tail6=$(echo "$mac" | sed 's/.*\([0-9A-F]\{6\}\)$/\1/')
[ -n "$tail6" ] || tail6="000000"
BT_NAME="CameVision Ego Single $tail6"
echo "mac=$mac name=$BT_NAME"
hciconfig hci0 name "$BT_NAME"
hciconfig hci0 class 0x000100
hciconfig hci0 piscan
bluetoothctl system-alias "$BT_NAME"
bluetoothctl pairable on
bluetoothctl discoverable-timeout 0
bluetoothctl discoverable on
printf '%s\n' 'menu advertise' 'clear' 'name on' 'discoverable on' 'tx-power on' 'back' | bluetoothctl
setsid /bin/sh /userdata/camevision-ble.sh </dev/null >/userdata/ble-adv.log 2>&1 &
echo $! >/tmp/camevision-ble.pid
sleep 1
echo "===HCI==="
hciconfig -a | grep -E 'Name:|BD Address|UP RUNNING'
echo "===CTL==="
bluetoothctl show | grep -E 'Alias|Name:|ActiveInstances|Discoverable:'
echo "===IP==="
ip -4 addr show wlan0 | grep inet
