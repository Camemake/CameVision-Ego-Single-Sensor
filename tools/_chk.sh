echo UPTIME; cat /proc/uptime
echo IDP; cat /sys/kernel/config/usb_gadget/rockchip/idProduct 2>/dev/null
echo IDV; cat /sys/kernel/config/usb_gadget/rockchip/idVendor 2>/dev/null
echo UDC; cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null
echo STATE; cat /sys/class/udc/21500000.usb/state 2>/dev/null
echo SPEED; cat /sys/class/udc/21500000.usb/current_speed 2>/dev/null
echo CFG; cat /tmp/.usb_config 2>/dev/null
echo FUNCS; ls /sys/kernel/config/usb_gadget/rockchip/configs/b.1/ 2>/dev/null
echo VIDEO; ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo VDEV; ls /dev/video* 2>/dev/null
echo STR; cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product 2>/dev/null
echo SER; cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/serialnumber 2>/dev/null
echo PUMP; cat /userdata/cv-uvc-pump.log 2>/dev/null
echo BLOG; tail -30 /userdata/cv-uvc-bridge.log 2>/dev/null
echo PS; ps | grep -E 'adbd|bridge|single_live|S50' | grep -v grep
echo WLAN; ip addr show wlan0 2>/dev/null | head -8
echo DMESG; dmesg | grep -E 'uvc|gadget|dwc3|UDC|failed to start|camemake|rockchip' | tail -40
