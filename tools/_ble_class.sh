#!/bin/sh
cd /userdata
wget -q -O camevision-agent-bt.sh http://192.168.1.44:18765/camevision-agent-bt.sh
sed -i 's/\r$//' camevision-agent-bt.sh
chmod 755 camevision-agent-bt.sh
hciconfig hci0 class 0x000620 2>/dev/null || true
hciconfig hci0 name "CameVision-462C47" 2>/dev/null || true
bluetoothctl pairable on >/dev/null 2>&1 || true
echo '=== class ==='
hciconfig -a hci0 | grep -E 'Name|Class'
printf '%s\n' 'show' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Alias|Pairable|Discoverable|ActiveInstances'
echo CLASS
