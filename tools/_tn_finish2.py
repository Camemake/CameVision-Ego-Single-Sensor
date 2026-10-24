#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "ls -l /userdata/camevision_dbus.py /userdata/swt6621_fw/sv6160lite.nvbin; "
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "python3 -c 'import camevision_dbus,camevision_ble; print(\"imports_ok\")'; "
        "tail -25 /userdata/camevision-agent.log; echo TN2",
        wait=6,
    )
)
