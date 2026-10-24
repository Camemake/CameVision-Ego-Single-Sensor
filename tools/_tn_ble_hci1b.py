#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "cd /userdata; "
        "wget -q -O camevision_ble.py http://192.168.1.44:18767/camevision_ble.py; "
        "kill $(ps | grep '[c]amevision_agent.py' | awk '{print $1}') 2>/dev/null; sleep 1; "
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "python3 -c 'from camevision_ble import _hci_name,_mac_tail,advert_name; print(_hci_name(), _mac_tail(), advert_name())'; "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; "
        "sleep 6; "
        "echo ===LOG===; tail -12 /userdata/camevision-agent.log; "
        "echo ===STATUS===; wget -q -O - http://127.0.0.1:8090/v1/status; echo; "
        "dd if=/dev/mmcblk1p1 bs=512 count=1 of=/tmp/fatboot.bin 2>/dev/null; "
        "python3 -c 'b=open(\"/tmp/fatboot.bin\",\"rb\").read(); print(\"boot\",len(b),hex(b[510]),hex(b[511]), b[11]+256*b[12], b[32]+(b[33]<<8)+(b[34]<<16)+(b[35]<<24))'; "
        "echo HCI1B_DONE",
        wait=16,
    )
)
