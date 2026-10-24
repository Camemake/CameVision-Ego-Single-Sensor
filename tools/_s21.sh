echo ===S21===
grep -n 'usb\|adbd\|gadget\|S50' /etc/init.d/S21appinit /etc/init.d/S20linkmount /etc/init.d/S10udev 2>/dev/null | head -40
echo ===USERDATA_S50===
head -5 /userdata/S50usbdevice
echo ===STOP===
cat /userdata/camevision-uvc-stop.sh
echo ===START===
cat /userdata/camevision-uvc-start.sh
echo ===S99===
cat /etc/init.d/S99camevision-single
echo ===rcS===
grep -n usb /etc/init.d/rcS /etc/inittab 2>/dev/null
