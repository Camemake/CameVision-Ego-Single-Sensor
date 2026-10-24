grep -n 'usb\|adbd\|gadget\|uvc\|S50\|stop' /userdata/camevision-single.sh | head -50
echo ===FILE===
wc -l /userdata/camevision-single.sh
echo ===S99cv===
cat /etc/init.d/S99camevision
