mkdir -p /userdata/cv-s50-bak
wget -q -O /tmp/official.sh http://192.168.1.44:18765/_official.sh
sed -i 's/\r$//' /tmp/official.sh
trap '' HUP
sh /tmp/official.sh
echo OFFICIAL_DONE
