wget -q -O /tmp/install_s50.sh http://192.168.1.44:18765/_install_s50.sh
sed -i 's/\r$//' /tmp/install_s50.sh
sh /tmp/install_s50.sh
