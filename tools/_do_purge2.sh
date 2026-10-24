wget -q -O /tmp/purge2.sh http://192.168.1.44:18765/_purge2.sh
sed -i 's/\r$//' /tmp/purge2.sh
trap '' HUP
sh /tmp/purge2.sh
echo P2_DONE
