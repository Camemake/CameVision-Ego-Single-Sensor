#!/bin/sh
echo '=== wifi ==='
ip -4 addr show wlan0 | awk '/inet /{print $2}'
echo '=== hci ==='
hciconfig -a hci0
echo '=== procs ==='
ps | grep -E '[c]amevision_agent.py|[b]luetoothd|[b]luetoothctl|[c]amevision-ble'
echo '=== ctl ==='
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Name|Alias|Powered|Discoverable|Pairable|ActiveInstances|SupportedInstances|UUID|Advertising'
echo '=== log ==='
tail -12 /userdata/camevision-agent.log
echo '=== tools ==='
ls /usr/bin/hcitool /usr/bin/hciconfig /usr/bin/btmgmt /usr/bin/hcidump 2>/dev/null
hcitool -h 2>&1 | head -20
echo DIAG
