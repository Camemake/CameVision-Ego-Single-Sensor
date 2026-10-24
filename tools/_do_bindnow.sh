wget -q -O /tmp/bindnow.sh http://192.168.1.44:18765/_bindnow.sh
sed -i 's/\r$//' /tmp/bindnow.sh
trap '' HUP
sh /tmp/bindnow.sh
echo BINDNOW_DONE
