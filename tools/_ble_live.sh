#!/bin/sh
echo '=== wifi ==='
ip -4 addr show wlan0 | awk '/inet /{print $2}'
echo '=== hci ==='
hciconfig hci0
echo '=== ps ==='
ps | grep -E '[c]amevision-ble.sh|[c]amevision_agent|[b]luetoothctl|[b]luetoothd'
echo '=== ctl ==='
printf '%s\n' 'show' 'menu advertise' 'name' 'secondary' 'back' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Name|Alias|Powered|ActiveInstances|LocalName|Secondary|RSI|Discoverable|Advertising'
echo LIVE
