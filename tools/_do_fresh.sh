wget -q -O /tmp/fresh.sh http://192.168.1.44:18765/_fresh.sh
sed -i 's/\r$//' /tmp/fresh.sh
trap '' HUP
sh /tmp/fresh.sh
echo FRESH_DONE
