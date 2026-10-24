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
    def log_message(self, *_args):
        return


def main() -> None:
    os.chdir(TOOLS)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", PORT), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.2)
    url = "http://%s:%s/camevision-usb-sd.sh" % (HOST, PORT)
    cmd = (
        "python3 -c \"import urllib.request,os;"
        "urllib.request.urlretrieve('" + url + "','/userdata/camevision-usb-sd.sh');"
        "print(os.path.getsize('/userdata/camevision-usb-sd.sh'))\"; "
        "sed -i 's/\\r$//' /userdata/camevision-usb-sd.sh; "
        "chmod 755 /userdata/camevision-usb-sd.sh; "
        "kill $(cat /tmp/camevision-agent.pid) 2>/dev/null; "
        "killall camevision-usb-sd.sh 2>/dev/null; "
        "sleep 1; "
        "sync; umount /mnt/sdcard; "
        "echo after_umount; grep sdcard /proc/mounts || echo unmounted; "
        "export PYTHONPATH=/userdata:/userdata/pylib; "
        "setsid /usr/bin/python3 /userdata/camevision_agent.py >>/userdata/camevision-agent.log 2>&1 & "
        "echo $! >/tmp/camevision-agent.pid; "
        "setsid /bin/sh /userdata/camevision-usb-sd.sh </dev/null >>/userdata/cv-usb-sd.log 2>&1 & "
        "sleep 2; "
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo MNT; grep sdcard /proc/mounts || echo none; "
        "tail -6 /userdata/cv-usb-sd.log"
    )
    print(cv_tn.run(cmd, wait=12.0))
    httpd.shutdown()


if __name__ == "__main__":
    main()
