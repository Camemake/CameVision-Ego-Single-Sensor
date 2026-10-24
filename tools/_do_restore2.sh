wget -q -O /tmp/restore2.sh http://192.168.1.44:18765/_restore2.sh
sed -i 's/\r$//' /tmp/restore2.sh
sh /tmp/restore2.sh
