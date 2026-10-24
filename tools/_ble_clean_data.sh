#!/bin/sh
# Drop every advert instance, then one packet with AD type 0x09 name.
killall bluetoothctl 2>/dev/null || true
sleep 1
printf '%s\n' 'advertise off' 'advertise off' 'advertise off' 'quit' | bluetoothctl
sleep 1
name_hex='43 61 6d 65 56 69 73 69 6f 6e 2d 34 36 32 43 34 37'
setsid /bin/sh -c "
{
	printf '%s\\n' \
		'agent NoInputNoOutput' \
		'default-agent' \
		'advertise off' \
		'menu advertise' \
		'clear' \
		'rsi off' \
		'secondary 1M' \
		'interval 100 150' \
		'tx-power off' \
		'data 0x09 data=$name_hex' \
		'name CameVision-462C47' \
		'discoverable on' \
		'back' \
		'advertise on'
	sleep infinity
} | exec bluetoothctl
" </dev/null >/userdata/ble-adv.log 2>&1 &
echo $! >/tmp/camevision-ble.pid
sleep 2
echo '=== log ==='
grep -E 'Invalid|Failed|LocalName|data 0x09|ActiveInstances|RSI' /userdata/ble-adv.log | tail -20
echo CLEAN
