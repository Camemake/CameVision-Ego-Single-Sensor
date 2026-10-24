#!/bin/sh
# Program sdmmc0 3.3 V boot + SD mount helpers. Allowed board only.
set -e
SER=$(cat /proc/device-tree/serial-number 2>/dev/null | tr -d '\000')
USB=$(cat /sys/class/android_usb/android0/iSerial 2>/dev/null || true)
echo "serial $SER usb $USB"
if [ "$SER" = "0558fa189447bc45" ] || [ "$USB" = "0558fa189447bc45" ]; then
	echo "REFUSE gen1"
	exit 2
fi
if [ "$SER" != "e4feca993701b30c" ] && [ "$USB" != "e4feca993701b30c" ]; then
	echo "REFUSE unexpected serial"
	exit 2
fi
HOST=http://192.168.1.44:18765
cd /userdata
dd if=/dev/mmcblk0p4 of=/userdata/boot-pre-sd.img bs=65536 2>/tmp/dd-pre.err || true
wget -q -O camevision-sd.sh "$HOST/camevision-sd.sh"
wget -q -O camevision-hw.sh "$HOST/camevision-hw.sh"
wget -q -O camevision_agent.py "$HOST/camevision_agent.py"
wget -q -O /tmp/camevision_boot_mono_wifi.img "$HOST/camevision_boot_mono_wifi.img"
sed -i 's/\r$//' camevision-sd.sh camevision-hw.sh camevision_agent.py
chmod 755 camevision-sd.sh camevision-hw.sh
SZ=$(wc -c < /tmp/camevision_boot_mono_wifi.img)
echo "boot bytes $SZ"
if [ "$SZ" -lt 10000000 ] || [ "$SZ" -gt 12000000 ]; then
	echo "bad boot size"
	exit 3
fi
dd if=/tmp/camevision_boot_mono_wifi.img of=/dev/mmcblk0p4 bs=65536 conv=fsync
sync
echo PROGRAM_OK
reboot
