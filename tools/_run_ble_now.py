#!/usr/bin/env python3
"""Bring BLE up via telnet. Avoids PowerShell $(...) and \\r expansion."""
from cv_tn import run

print(run("wget -q -O /tmp/_ble_up.sh http://192.168.1.44:18767/_ble_up.sh; sh /tmp/_ble_up.sh", wait=75))
