wget -q -O /tmp/install_first.sh http://192.168.1.44:18765/_install_first.sh
sed -i 's/\r$//' /tmp/install_first.sh
sh /tmp/install_first.sh
