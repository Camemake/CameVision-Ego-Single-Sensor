#!/bin/sh
printf '%s\n' 'devices' 'disconnect' 'remove E0:C9:32:91:BC:9C' 'quit' | bluetoothctl
echo
echo '=== devices ==='
printf '%s\n' 'devices' 'quit' | bluetoothctl
echo DROP
