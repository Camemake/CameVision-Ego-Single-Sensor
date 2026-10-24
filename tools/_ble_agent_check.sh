#!/bin/sh
echo '=== files ==='
ls -l /userdata/camevision_agent.py /userdata/camevision_ble.py /userdata/camevision-ble.sh 2>/dev/null
echo '=== agent log files ==='
ls -l /userdata/camevision-agent.log /tmp/camevision-agent.log /tmp/camevision-agent.pid 2>/dev/null
echo '=== dbus ==='
ls /usr/lib/python3*/site-packages/dbus 2>/dev/null | head
python3 -c 'import dbus,dbus.mainloop.glib; from gi.repository import GLib; print("dbus-ok")' 2>&1 | tail -5
echo '=== python path ==='
echo "PYTHONPATH=$PYTHONPATH"
ls /userdata/pylib 2>/dev/null | head
echo AGENT_CHECK
