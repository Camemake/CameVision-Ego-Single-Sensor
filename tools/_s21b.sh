echo ===S21===
cat /etc/init.d/S21appinit
echo ===S20===
cat /etc/init.d/S20linkmount
echo ===userdataS50refs===
grep -R 'userdata/S50\|usb_config.sh' /etc /userdata /oem --include='*.sh' 2>/dev/null | head
echo ===single===
cat /userdata/camevision-single.sh
