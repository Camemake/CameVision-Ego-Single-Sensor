#!/usr/bin/env python3
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
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.3)
    base = "http://%s:%s" % (HOST, PORT)
    names = (
        "camevision_agent.py",
        "camevision-uvc-bridge.py",
        "_lock_uvc_safe.sh",
        "camevision-usb-sd.sh",
    )
    py = [
        "import urllib.request, os",
        "os.chdir('/userdata')",
    ]
    for name in names:
        dst = "/userdata/" + name
        py.append("urllib.request.urlretrieve('%s/%s', '%s')" % (base, name, dst))
        py.append("print('%s', os.path.getsize('%s'))" % (name, dst))
    fetch = "python3 -c \"%s\"" % ("; ".join(py),)
    cmd = (
        fetch + "; "
        "sed -i 's/\\r$//' /userdata/_lock_uvc_safe.sh /userdata/camevision-usb-sd.sh "
        "/userdata/camevision-uvc-bridge.py /userdata/camevision_agent.py; "
        "chmod 755 /userdata/_lock_uvc_safe.sh /userdata/camevision-usb-sd.sh; "
        "sh /userdata/_lock_uvc_safe.sh"
    )
    print(cv_tn.run(cmd, wait=28.0))
    httpd.shutdown()


if __name__ == "__main__":
    main()
