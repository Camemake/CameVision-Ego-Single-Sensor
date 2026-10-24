#!/bin/sh
# Phone Settings scan is classic inquiry. Discoverable timed out at 180s.
bluetoothctl power on >/dev/null 2>&1 || true
bluetoothctl discoverable-timeout 0 >/dev/null 2>&1 || true
bluetoothctl pairable on >/dev/null 2>&1 || true
bluetoothctl discoverable on >/dev/null 2>&1 || true
bluetoothctl system-alias "CameVision Ego Single 462C47" >/dev/null 2>&1 || true
hciconfig hci0 name "CameVision Ego Single 462C47" 2>/dev/null || true
hciconfig hci0 class 0x000100 2>/dev/null || true
hciconfig hci0 piscan 2>/dev/null || true
sleep 1
echo '=== show ==='
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Name|Alias|Powered|Discoverable|Pairable|ActiveInstances'
echo '=== hci ==='
hciconfig -a hci0 | grep -E 'UP|Name|Class|PSCAN|ISCAN'
ip -4 addr show wlan0 | awk '/inet /{print $2}'
echo PHONE_ON
