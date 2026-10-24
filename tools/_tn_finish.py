#!/usr/bin/env python3
from cv_tn import run

print("=== agent ===")
print(
    run(
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "if ! wget -q -O /dev/null http://127.0.0.1:8090/v1/status; then "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; sleep 2; fi; "
        "wget -q -O - http://127.0.0.1:8090/v1/status; echo; "
        "ip -4 addr show wlan0 | head -4; "
        "hciconfig hci0; "
        "df -h /mnt/sdcard; "
        "tail -8 /userdata/camevision-agent.log; echo TN1",
        wait=8,
    )
)
