#!/bin/sh
echo '=== wifi ==='
ip -4 addr show wlan0 | awk '/inet /{print $2}'
echo '=== hci ==='
hciconfig -a hci0 | grep -E 'UP|Name|Class|PSCAN|ISCAN|Address'
echo '=== procs ==='
ps | grep -E '[c]amevision_agent.py|[b]luetoothd'
echo '=== ctl ==='
printf '%s\n' 'show' 'devices' 'paired-devices' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Alias|Powered|Discoverable|Pairable|ActiveInstances|Device |UUID|Name'
echo '=== log ==='
tail -8 /userdata/camevision-agent.log
echo CONN
