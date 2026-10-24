wget -q -O /tmp/switch.sh http://192.168.1.44:18765/_switch.sh
sed -i 's/\r$//' /tmp/switch.sh
trap '' HUP
sh /tmp/switch.sh
echo SWITCH_DONE
