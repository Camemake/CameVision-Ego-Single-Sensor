#!/usr/bin/env python3
"""Push agent + BLE GATT to the live board and restart only the agent."""
from __future__ import annotations

import http.server
import os
import socketserver
import threading
import time
from pathlib import Path

import cv_tn

TOOLS = Path(__file__).resolve().parent
PORT = 18769
HOST = "192.168.1.44"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("HTTP", args[0] if args else fmt, flush=True)


def main() -> None:
    os.chdir(TOOLS)
    agent_n = (TOOLS / "camevision_agent.py").stat().st_size
    ble_n = (TOOLS / "camevision_ble.py").stat().st_size
    dbus_n = (TOOLS / "camevision_dbus.py").stat().st_size
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.4)
    base = "http://%s:%s" % (HOST, PORT)
    cmd = (
        "cd /userdata; "
        "python3 -c \"import urllib.request; "
        "urllib.request.urlretrieve('%s/camevision_agent.py','/userdata/camevision_agent.py'); "
        "urllib.request.urlretrieve('%s/camevision_ble.py','/userdata/camevision_ble.py'); "
        "urllib.request.urlretrieve('%s/camevision_dbus.py','/userdata/camevision_dbus.py'); "
        "urllib.request.urlretrieve('%s/_agent_only_restart.sh','/tmp/_agent_only_restart.sh'); "
        "print('got', __import__('os').path.getsize('/userdata/camevision_agent.py'), "
        "__import__('os').path.getsize('/userdata/camevision_ble.py'), "
        "__import__('os').path.getsize('/userdata/camevision_dbus.py'))\"; "
        "sed -i 's/\\r$//' /tmp/_agent_only_restart.sh; "
        "chmod 755 /tmp/_agent_only_restart.sh; "
        "sh /tmp/_agent_only_restart.sh"
    ) % (base, base, base, base)
    print("expect", agent_n, ble_n, dbus_n, flush=True)
    print(cv_tn.run(cmd, wait=14.0))
    time.sleep(0.2)
    httpd.shutdown()


if __name__ == "__main__":
    main()
