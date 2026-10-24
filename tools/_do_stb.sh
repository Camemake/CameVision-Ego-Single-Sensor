wget -q -O /tmp/stb.sh http://192.168.1.44:18765/_stop_then_bind.sh
sed -i 's/\r$//' /tmp/stb.sh
trap '' HUP
sh /tmp/stb.sh
echo STB_DONE
