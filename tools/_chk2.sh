echo F1; readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f1
echo F2; readlink /sys/kernel/config/usb_gadget/rockchip/configs/b.1/f2
echo MAX; cat /sys/kernel/config/usb_gadget/rockchip/max_speed 2>/dev/null
echo CTRL; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/control/class/ 2>/dev/null
echo STRM; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/streaming/class/ 2>/dev/null
echo MJ; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/streaming/mjpeg/m/ 2>/dev/null
echo UVCATTR; ls /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/ 2>/dev/null
echo DNAME; cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/device_name 2>/dev/null
echo FNAME; cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/function_name 2>/dev/null
echo SMP; cat /sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs6/streaming_maxpacket 2>/dev/null
echo INITD; ls /etc/init.d/S50* /etc/init.d/S99* 2>/dev/null
echo UD; ls /userdata/*uvc* /userdata/*g.sh /userdata/camevision* 2>/dev/null
echo USBDEV; ls -l /usr/bin/usbdevice; head -3 /usr/bin/usbdevice
echo UDEV; ls /lib/udev/rules.d/*usbdevice* 2>/dev/null
echo UDCATTR; ls /sys/class/udc/21500000.usb/
echo DWC; ls /sys/bus/platform/drivers/dwc3/ 2>/dev/null
echo DWC3; ls /sys/devices/platform/21500000.usb/ 2>/dev/null | head
echo ROLE; ls /sys/class/usb_role/ 2>/dev/null
echo SOFT; ls /sys/class/udc/21500000.usb/device/ 2>/dev/null | head -30
