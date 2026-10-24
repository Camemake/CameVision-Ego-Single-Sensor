#!/bin/sh
grep -E 'data |Failed|error|Invalid|09|CameVision|Type' /userdata/ble-adv.log | tail -30
echo '---'
printf '%s\n' 'menu advertise' 'data' 'back' 'quit' | bluetoothctl | sed 's/\x1b\[[0-9;]*m//g' | tail -25
echo DATA
