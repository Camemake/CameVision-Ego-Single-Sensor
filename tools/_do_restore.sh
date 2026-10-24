wget -q -O /tmp/restore_adb.sh http://192.168.1.44:18765/_restore_adb.sh
sed -i 's/\r$//' /tmp/restore_adb.sh
sh /tmp/restore_adb.sh
