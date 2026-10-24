#!/bin/sh
i=0
while [ "$i" -lt 20 ]; do
	mac=$(hciconfig hci0 2>/dev/null | awk '/BD Address/{print $3}')
	if [ -n "$mac" ] && [ "$mac" != "00:00:00:00:00:00" ]; then
		echo "MAC $mac"
		break
	fi
	i=$((i + 1))
	sleep 1
done
hciconfig hci0 up
hciconfig hci0 class 0x000620
setsid /bin/sh /userdata/camevision-ble.sh </dev/null >/userdata/ble-boot.log 2>&1 &
sleep 2
hciconfig hci0
wget -q -O - http://127.0.0.1:8090/ 2>/dev/null | head -c 500
echo
df -h /mnt/sdcard
