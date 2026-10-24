#!/bin/sh
printf '%s\n' 'discoverable off' 'quit' | bluetoothctl >/dev/null 2>&1 || true
sleep 1
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Alias|ActiveInstances|Discoverable'
ps | grep -E '[c]amevision_agent|[_]_ble_hold_name|bluetoothd'
echo '---HOLD---'
cat /userdata/ble-hold.log
echo DISC
