#!/bin/sh
echo '=== procs ==='
ps | grep -E '[c]amevision_agent|[c]amevision-ble.sh|[b]luetoothctl|[b]luetoothd' || true
echo '=== wlan ==='
ip -4 addr show wlan0 | grep inet || echo NO_WIFI
echo '=== hci ==='
hciconfig hci0
echo '=== show ==='
printf '%s\n' 'show' 'quit' | bluetoothctl | sed 's/\x1b\[[0-9;]*m//g'
echo '=== adv log ==='
tail -20 /userdata/ble-adv.log | sed 's/\x1b\[[0-9;]*m//g'
echo '=== agent ==='
tail -8 /userdata/camevision-agent.log
echo NOW
