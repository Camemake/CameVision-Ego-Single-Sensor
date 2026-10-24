wget -q -O /tmp/cfgfs.sh http://192.168.1.44:18765/_cfgfs.sh
sed -i 's/\r$//' /tmp/cfgfs.sh
trap '' HUP
sh /tmp/cfgfs.sh
echo CFGFS_DONE
