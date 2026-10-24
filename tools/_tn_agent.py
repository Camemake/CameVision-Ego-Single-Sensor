#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "cd /userdata; wget -q -O camevision_agent.py http://192.168.1.44:18767/camevision_agent.py; "
        "wc -c camevision_agent.py; "
        "kill $(ps | grep '[c]amevision_agent.py' | awk '{print $1}') 2>/dev/null; sleep 1; "
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; sleep 2; "
        "wget -q -O - http://127.0.0.1:8090/v1/status; echo; echo AGENT_OK",
        wait=10,
    )
)
