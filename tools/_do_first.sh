wget -q -O /tmp/first.sh http://192.168.1.44:18765/_first.sh
sed -i 's/\r$//' /tmp/first.sh
trap '' HUP
sh /tmp/first.sh
echo FIRST_DONE
