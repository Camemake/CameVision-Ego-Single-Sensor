cp -f /oem/usr/share/rkuvc.ini /tmp/rkuvc.ini
: > /userdata/cv-rk-mpi-uvc.log
setsid /oem/usr/bin/rk_mpi_uvc -c /tmp/rkuvc.ini -a /oem/usr/share/iqfiles </dev/null >>/userdata/cv-rk-mpi-uvc.log 2>&1 &
echo MPI $!
sleep 6
echo ---log---
tail -40 /userdata/cv-rk-mpi-uvc.log
echo ---gadget---
echo ID=$(cat /sys/kernel/config/usb_gadget/rockchip/idProduct 2>/dev/null)
echo UDC=$(cat /sys/kernel/config/usb_gadget/rockchip/UDC 2>/dev/null)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
ls /sys/class/udc/21500000.usb/device/gadget.0/video4linux/ 2>/dev/null
echo ---ps---
ps | grep -E 'rk_mpi_uvc|adbd|single_live' | grep -v grep
dmesg | tail -8
# stop mpi so it does not fight single_live
killall rk_mpi_uvc 2>/dev/null || true
