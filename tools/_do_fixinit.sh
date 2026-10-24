wget -q -O /tmp/fixinit.sh http://192.168.1.44:18765/_fixinit.sh
sed -i 's/\r$//' /tmp/fixinit.sh
sh /tmp/fixinit.sh
