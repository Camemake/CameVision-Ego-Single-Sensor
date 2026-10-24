#!/bin/sh
echo '=== alias ==='
printf '%s\n' 'show' 'quit' | bluetoothctl | grep -E 'Alias|Name:|ActiveInstances|Discoverable'
echo '=== hci name ==='
hciconfig -a | grep -E 'Name:|BD Address|Class'
echo '=== adv name lines ==='
grep -E 'LocalName|name on|Name:|secondary|interval' /userdata/ble-adv.log | tail -20
echo CHECK
