#!/bin/sh
cd /userdata
if [ -f /tmp/camevision-agent.pid ]; then
	kill "$(cat /tmp/camevision-agent.pid)" 2>/dev/null
	sleep 1
fi
python3 -c "import os,signal
for p in os.listdir('/proc'):
    if not p.isdigit():
        continue
    try:
        data=open('/proc/%s/cmdline'%p,'rb').read()
    except OSError:
        continue
    if b'camevision_agent.py' in data:
        os.kill(int(p),15)
"
sleep 1
export PYTHONPATH=/userdata:/userdata/pylib
setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 &
echo $! >/tmp/camevision-agent.pid
sleep 3
wc -c /userdata/camevision_agent.py /userdata/camevision_ble.py /userdata/camevision_dbus.py
tail -12 /userdata/camevision-agent.log
