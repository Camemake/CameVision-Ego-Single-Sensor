#!/bin/sh
echo '=== tools ==='
command -v btmon; command -v hcidump; command -v btmgmt; command -v hcitool
echo '=== leadv ==='
printf '%s\n' 'advertise off' 'quit' | bluetoothctl >/dev/null 2>&1
sleep 1
hciconfig hci0 leadv 0; echo leadv0=$?
hciconfig hci0 leadv 3; echo leadv3=$?
hciconfig hci0 leadv
echo '=== back on ==='
printf '%s\n' 'menu advertise' 'name on' 'discoverable on' 'tx-power on' 'back' 'advertise on' 'quit' | bluetoothctl | grep -E 'LocalName|Name:|Active|error|Failed|advertis'
echo RAW
