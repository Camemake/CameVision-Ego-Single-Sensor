wget -q -O /tmp/patch_s50.sh http://192.168.1.44:18765/_patch_s50.sh
sed -i 's/\r$//' /tmp/patch_s50.sh
sh /tmp/patch_s50.sh
