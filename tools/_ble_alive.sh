#!/bin/sh
hciconfig -a hci0 2>&1 | head -16
ip -4 addr show wlan0 | awk '/inet /{print $2}'
ps | grep -E '[c]amevision_agent.py|[b]luetoothd'
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Powered|Discoverable|Pairable|ActiveInstances|Alias'
echo ALIVE
