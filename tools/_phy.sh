echo PHY
cat /sys/devices/platform/21400000.usb2-phy/otg_mode 2>/dev/null
ls /sys/devices/platform/21400000.usb2-phy/ 2>/dev/null
echo ROLE
cat /sys/class/udc/21500000.usb/device/role 2>/dev/null
ls /sys/class/udc/21500000.usb/
echo EXTCON
cat /sys/class/extcon/extcon0/state 2>/dev/null
find /sys/devices/platform/21400000.usb2-phy /sys/class/extcon -name state -o -name otg_mode -o -name role 2>/dev/null | while read f; do echo $f=$(cat $f); done
echo SET_PERIPH
echo peripheral > /sys/devices/platform/21400000.usb2-phy/otg_mode
sleep 1
echo PHY2
cat /sys/devices/platform/21400000.usb2-phy/otg_mode
echo STATE
cat /sys/class/udc/21500000.usb/state
printf '21500000.usb' > /sys/kernel/config/usb_gadget/rockchip/UDC
echo BIND_RC $?
cat /sys/kernel/config/usb_gadget/rockchip/UDC
cat /sys/class/udc/21500000.usb/state
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
dmesg | tail -8
