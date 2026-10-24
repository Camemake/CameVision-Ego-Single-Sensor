wget -q -O /tmp/purge.sh http://192.168.1.44:18765/_purge.sh
sed -i 's/\r$//' /tmp/purge.sh
trap '' HUP
sh /tmp/purge.sh
echo PURGE_DONE
