#!/usr/bin/env python3
from cv_tn import run

print(run(
    "hciconfig hci0; echo ---; ls -l /userdata/camevision_dbus.py /userdata/camevision_agent.py /userdata/camevision-ble.sh; echo ---; wget -S -O /tmp/dbus_chk.py http://192.168.1.44:18767/camevision_dbus.py; wc -c /tmp/dbus_chk.py; echo ---; wget -S -O /tmp/dbus_chk2.py http://192.168.1.44:18766/camevision_dbus.py; wc -c /tmp/dbus_chk2.py; echo ---; ps | grep -E 'camevision|bluetooth|skwbt' | grep -v grep; echo ---; cat /proc/skwsdio/bt_service 2>/dev/null; echo; tail -20 /userdata/camevision-agent.log; echo DIAG_OK",
    wait=20,
))
