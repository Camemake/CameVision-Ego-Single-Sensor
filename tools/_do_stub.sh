wget -q -O /tmp/s50stub.sh http://192.168.1.44:18765/_s50stub.sh
sed -i 's/\r$//' /tmp/s50stub.sh
sh /tmp/s50stub.sh
