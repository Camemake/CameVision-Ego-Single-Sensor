#!/bin/sh
cd /userdata
wget -q -O _lock_uvc_safe.sh http://192.168.1.44:18765/_lock_uvc_safe.sh
wget -q -O camevision-uvc-bridge.py http://192.168.1.44:18765/camevision-uvc-bridge.py
wget -q -O single_live.py http://192.168.1.44:18765/single_live.py
sed -i 's/\r$//' _lock_uvc_safe.sh camevision-uvc-bridge.py single_live.py
chmod 755 _lock_uvc_safe.sh
sh /userdata/_lock_uvc_safe.sh
echo REBIND_DONE
