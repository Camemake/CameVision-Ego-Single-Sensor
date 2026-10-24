wget -q -O /tmp/yank.sh http://192.168.1.44:18765/_yank.sh
sed -i 's/\r$//' /tmp/yank.sh
trap '' HUP
sh /tmp/yank.sh
echo YANK_DONE
