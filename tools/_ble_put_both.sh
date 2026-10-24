#!/bin/sh
cd /userdata
wget -q -O camevision_agent.py http://192.168.1.44:18765/camevision_agent.py
wget -q -O camevision_ble.py http://192.168.1.44:18765/camevision_ble.py
sed -i 's/\r$//' camevision_agent.py camevision_ble.py
for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do
	kill "$p" 2>/dev/null || true
done
sleep 2
export PYTHONPATH=/userdata/pylib
setsid /usr/bin/python3 /userdata/camevision_agent.py </dev/null >>/userdata/camevision-agent.log 2>&1 &
sleep 3
wget -q -O - http://127.0.0.1:8090/v1/status
echo
echo PUT_BOTH
