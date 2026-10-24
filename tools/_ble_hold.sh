#!/bin/sh
# Hold advertise after the alias is already set. Do not kill bluetoothd.
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
printf '%s\n' 'menu advertise' 'name on' 'discoverable on' 'tx-power on' 'back' | bluetoothctl
exec bluetoothctl advertise on
