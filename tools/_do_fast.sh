wget -q -O /tmp/fast.sh http://192.168.1.44:18765/_fast.sh
sed -i 's/\r$//' /tmp/fast.sh
trap '' HUP
sh /tmp/fast.sh
echo FAST_DONE
