#!/bin/sh
set -e
cd /userdata
wget -q -O _lock_uvc_safe.sh http://192.168.1.44:18765/_lock_uvc_safe.sh
wget -q -O camevision-uvc-bridge.py http://192.168.1.44:18765/camevision-uvc-bridge.py
wget -q -O single_live.py http://192.168.1.44:18765/single_live.py
sed -i 's/\r$//' _lock_uvc_safe.sh camevision-uvc-bridge.py single_live.py
chmod 755 _lock_uvc_safe.sh
# Restart live without killing the recorder/agent.
for p in $(ps | grep '[s]ingle_live.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
sleep 1
export PYTHONPATH=/userdata/pylib
setsid /usr/bin/python3 /userdata/single_live.py </dev/null >/userdata/single-live.log 2>&1 &
sleep 3
sh /userdata/_lock_uvc_safe.sh
echo APPLY_DONE
