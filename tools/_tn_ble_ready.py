#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "bluetoothctl power on; "
        "bluetoothctl system-alias CameVision-462C47; "
        "bluetoothctl pairable on; "
        "bluetoothctl discoverable on; "
        "hciconfig hci0 class 0x000620; "
        "hciconfig hci0 piscan; "
        "hciconfig hci0 name CameVision-462C47; "
        "for p in $(ps | grep '[c]amevision-ble.sh' | awk '{print $1}'); do kill $p; done; "
        "for p in $(ps | grep '[c]amevision_agent.py' | awk '{print $1}'); do kill $p; done; "
        "sleep 1; "
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; "
        "setsid /bin/sh /userdata/camevision-ble.sh >/userdata/ble-adv.log 2>&1 & "
        "echo $! >/tmp/camevision-ble.pid; "
        "sleep 5; "
        "bluetoothctl show; "
        "echo ===HCI===; hciconfig hci0; "
        "echo ===STATUS===; wget -q -O - http://127.0.0.1:8090/v1/status; echo; "
        "echo ===LOG===; tail -20 /userdata/camevision-agent.log; "
        "echo READY_DONE",
        wait=16,
    )
)
