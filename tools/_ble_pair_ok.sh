#!/bin/sh
# Accept Just Works pairing. Computer CoD makes Android say
# "Can't communicate with Camevision" after a Settings tap.
cd /userdata
for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
killall bluetoothctl 2>/dev/null || true
sleep 1
# Drop a half-open LE/classic link from the phone Settings tap.
printf '%s\n' 'devices' 'disconnect' 'quit' | bluetoothctl >/dev/null 2>&1 || true
bluetoothctl power on >/dev/null 2>&1 || true
bluetoothctl discoverable-timeout 0 >/dev/null 2>&1 || true
bluetoothctl pairable on >/dev/null 2>&1 || true
bluetoothctl discoverable on >/dev/null 2>&1 || true
bluetoothctl system-alias "CameVision-462C47" >/dev/null 2>&1 || true
hciconfig hci0 name "CameVision-462C47" 2>/dev/null || true
# Imaging / camera, not Computer — Settings will not treat it as a PC.
hciconfig hci0 class 0x000680 2>/dev/null || true
hciconfig hci0 piscan 2>/dev/null || true
# One bluetoothctl must stay as the pairing agent.
cat > /userdata/camevision-agent-bt.sh <<'EOF'
#!/bin/sh
{
	printf '%s\n' \
		'agent NoInputNoOutput' \
		'default-agent' \
		'pairable on' \
		'discoverable on'
	sleep infinity
} | exec bluetoothctl
EOF
sed -i 's/\r$//' /userdata/camevision-agent-bt.sh
chmod 755 /userdata/camevision-agent-bt.sh
setsid /bin/sh /userdata/camevision-agent-bt.sh </dev/null >/userdata/ble-agent.log 2>&1 &
sleep 1
echo '=== show ==='
printf '%s\n' 'show' 'devices' 'quit' | bluetoothctl 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'Alias|Discoverable|Pairable|ActiveInstances|Device |Class'
hciconfig -a hci0 | grep -E 'Name|Class|PSCAN|ISCAN'
ps | grep -E '[c]amevision_agent.py|[b]luetoothctl|camevision-agent-bt'
echo PAIR_OK
