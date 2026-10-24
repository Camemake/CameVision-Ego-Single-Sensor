#!/bin/sh
echo '=== show ==='
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g'
echo '=== advert menu ==='
printf '%s\n' 'menu advertise' 'help' 'back' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | tail -40
echo '=== adv log ==='
cat /userdata/ble-adv.log | sed 's/\x1b\[[0-9;]*m//g' | tail -40
echo '=== agent ==='
tail -10 /userdata/camevision-agent.log
echo STATUS
