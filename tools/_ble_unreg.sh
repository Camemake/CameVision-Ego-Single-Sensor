#!/bin/sh
cd /userdata
wget -q -O _ble_unreg.py http://192.168.1.44:18765/_ble_unreg.py
sed -i 's/\r$//' _ble_unreg.py
python3 _ble_unreg.py
echo '=== logread ==='
(logread 2>/dev/null || cat /var/log/messages 2>/dev/null || true) | grep -iE 'advert|bluez|Failed' | tail -20
echo '=== leadv ==='
hciconfig hci0 leadv 2>&1 | tail -5
echo UNREG
