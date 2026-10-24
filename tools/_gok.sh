G=/sys/kernel/config/usb_gadget/rockchip
C=$G/configs/b.1
U=$G/functions/uvc.gs1
echo PRE STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)

# Prepare unused uvc.gs1 while gadget is live.
mkdir -p $U
echo Camemake > $U/device_name 2>/dev/null || true
echo Camemake > $U/function_name 2>/dev/null || true
echo 1024 > $U/streaming_maxpacket 2>/dev/null || true
echo 0 > $U/streaming_bulk 2>/dev/null || true
mkdir -p $U/control/header/h
ln -s $U/control/header/h $U/control/class/fs/h 2>/dev/null || true
ln -s $U/control/header/h $U/control/class/ss/h 2>/dev/null || true
_d=$U/streaming/mjpeg/m/1400_1600p
mkdir -p $_d
echo 1400 > $_d/wWidth
echo 1600 > $_d/wHeight
echo 333333 > $_d/dwDefaultFrameInterval
echo $((1400 * 1600 * 16 * 5)) > $_d/dwMinBitRate
echo $((1400 * 1600 * 16 * 30)) > $_d/dwMaxBitRate
echo $((1400 * 1600 * 2)) > $_d/dwMaxVideoFrameBufferSize
printf '333333\n666666\n1000000\n2000000\n' > $_d/dwFrameInterval
mkdir -p $U/streaming/header/h
ln -s $U/streaming/mjpeg/m $U/streaming/header/h/m 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/fs/h 2>/dev/null || true
ln -s $U/streaming/header/h $U/streaming/class/hs/h 2>/dev/null || true
rm -f $U/streaming/class/ss/h
echo PREPARED

# Dirty empty: UDC file clear, hope state stays configured after soft_connect quirk.
printf '' > $G/UDC
echo AFTER_EMPTY STATE=$(cat /sys/class/udc/21500000.usb/state) UDC=$(cat $G/UDC)

# Composite Camemake UVC+ADB, PID 0019
rm -f $C/f1 $C/f3
# keep f2=ffs.adb if present; put UVC on f1
ln -s $U $C/f1
printf '0x0200' > $G/bcdUSB
printf '0x2207' > $G/idVendor
printf '0x0019' > $G/idProduct
printf '0' > $G/bDeviceClass
printf '0' > $G/bDeviceSubClass
printf '0' > $G/bDeviceProtocol
echo Camemake > $G/strings/0x409/manufacturer
echo Camemake > $G/strings/0x409/product
echo CV-EGO01-CAM > $G/strings/0x409/serialnumber
echo uvc_adb > $C/strings/0x409/configuration
printf '21500000.usb' > $G/UDC
echo BIND_RC=$?
echo ID=$(cat $G/idProduct) UDC=$(cat $G/UDC) STATE=$(cat /sys/class/udc/21500000.usb/state) SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
ls /sys/class/video4linux/ 2>/dev/null | head
dmesg | tail -8
