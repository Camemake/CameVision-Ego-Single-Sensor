#!/bin/sh
echo '=== con ==='
hcitool con 2>&1
echo '=== devices ==='
printf '%s\n' 'devices' 'paired-devices' 'info' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Device |Connected|Paired|Bonded|Trusted|RSSI|Name|Address' | head -40
echo '=== drop ==='
# Remove every remembered peer so the phone can try a clean LE connect.
for mac in $(printf '%s\n' 'devices' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | awk '/Device /{print $2}'); do
	echo drop "$mac"
	printf '%s\n' "disconnect $mac" "remove $mac" 'quit' | bluetoothctl >/dev/null 2>&1 || true
done
printf '%s\n' 'disconnect' 'quit' | bluetoothctl >/dev/null 2>&1 || true
sleep 1
echo '=== after ==='
hcitool con 2>&1
printf '%s\n' 'devices' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep Device || echo none
hciconfig hci0 | head -5
echo DROP
