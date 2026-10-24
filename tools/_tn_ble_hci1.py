#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "cd /userdata; "
        "wget -q -O camevision_ble.py http://192.168.1.44:18767/camevision_ble.py; "
        "wget -q -O camevision-ble.sh http://192.168.1.44:18767/camevision-ble.sh; "
        "wget -q -O camevision_agent.py http://192.168.1.44:18767/camevision_agent.py; "
        "sed -i 's/\\r$//' camevision-ble.sh; chmod 755 camevision-ble.sh; "
        "ls /sys/class/bluetooth; "
        "cat /sys/class/bluetooth/hci1/address 2>/dev/null; echo; "
        "for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do kill $p; done; "
        "for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do kill $p; done; "
        "sleep 1; "
        "bluetoothctl power on; "
        "bluetoothctl system-alias CameVision-462C47; "
        "bluetoothctl pairable on; "
        "bluetoothctl discoverable on; "
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; "
        "setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 & "
        "echo $! >/tmp/camevision-ble.pid; "
        "sleep 6; "
        "bluetoothctl show; "
        "echo ===STATUS===; wget -q -O - http://127.0.0.1:8090/v1/status; echo; "
        "echo ===LOG===; tail -15 /userdata/camevision-agent.log; "
        "echo HCI1_DONE",
        wait=18,
    )
)
