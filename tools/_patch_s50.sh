mount -o remount,rw / 2>/dev/null || true
cp -a /etc/init.d/S50usbdevice /etc/init.d/S50usbdevice.cvpreuvc
sed -i 's/echo "usb_adb_en" >> $USB_CONFIG_FILE/echo "usb_adb_en" >> $USB_CONFIG_FILE; echo "usb_uvc_en" >> $USB_CONFIG_FILE/' /etc/init.d/S50usbdevice
sed -i 's/configure_uvc_resolution_mjpeg 1280 720/configure_uvc_resolution_mjpeg 1400 1600/' /etc/init.d/S50usbdevice
sed -i 's/CameVision Single/Camemake/' /etc/init.d/S50usbdevice
sed -i 's/"CameMake"/"Camemake"/' /etc/init.d/S50usbdevice
echo PATCH_OK
grep -n 'usb_uvc_en\|1400 1600\|Camemake\|CV_NO_RESTART' /etc/init.d/S50usbdevice
sync
reboot
