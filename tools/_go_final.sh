wget -q -O /tmp/lock2.sh http://192.168.1.44:18765/_lock2.sh
wget -q -O /tmp/ok.sh http://192.168.1.44:18765/_ok.sh
sed -i 's/\r$//' /tmp/lock2.sh /tmp/ok.sh
trap '' HUP
sh /tmp/lock2.sh
sh /tmp/ok.sh
echo FINAL_DONE
sleep 2
G=/sys/kernel/config/usb_gadget/rockchip
echo STILL_ID=$(cat $G/idProduct)
echo STILL_UDC=$(cat $G/UDC)
echo STILL_F1=$(readlink $G/configs/b.1/f1)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/
ps | grep camevision-uvc-bridge | grep -v grep
tail -20 /userdata/cv-uvc-bridge.log
cat /tmp/.usb_config
