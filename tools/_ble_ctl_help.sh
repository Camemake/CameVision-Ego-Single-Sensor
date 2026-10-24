#!/bin/sh
echo '=== uname ==='
uname -am
echo '=== libdbus ==='
ls /usr/lib/libdbus* /lib/libdbus* 2>/dev/null
echo '=== advertise help ==='
printf '%s\n' 'menu advertise' 'help' 'back' 'quit' | bluetoothctl 2>/dev/null | tail -40
echo '=== gatt help ==='
printf '%s\n' 'menu gatt' 'help' 'back' 'quit' | bluetoothctl 2>/dev/null | tail -50
echo CTL_HELP
