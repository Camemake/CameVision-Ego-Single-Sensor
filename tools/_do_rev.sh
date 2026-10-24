wget -q -O /tmp/rev.sh http://192.168.1.44:18765/_revert_boot_uvc.sh
sed -i 's/\r$//' /tmp/rev.sh
sh /tmp/rev.sh
