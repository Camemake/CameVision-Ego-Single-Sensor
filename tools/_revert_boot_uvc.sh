mount -o remount,rw / 2>/dev/null || true
sed -i 's/echo "usb_adb_en" >> $USB_CONFIG_FILE; echo "usb_uvc_en" >> $USB_CONFIG_FILE/echo "usb_adb_en" >> $USB_CONFIG_FILE/' /etc/init.d/S50usbdevice
grep -n 'usb_adb_en' /etc/init.d/S50usbdevice | head -5
sync
reboot
