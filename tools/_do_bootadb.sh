wget -q -O /tmp/bootadb.sh http://192.168.1.44:18765/_bootadb.sh
sed -i 's/\r$//' /tmp/bootadb.sh
sh /tmp/bootadb.sh
