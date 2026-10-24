echo SPEED=$(cat /sys/class/udc/21500000.usb/current_speed)
echo STATE=$(cat /sys/class/udc/21500000.usb/state)
echo FUNC=$(cat /sys/class/udc/21500000.usb/function)
echo ---mpi cfg---
head -40 /oem/usr/share/uvc_mpi_cfg.conf
