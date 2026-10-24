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
    base = "http://%s:%s" % (HOST, PORT)
    cmd = (
        "cd /userdata; "
        "python3 -c \"import urllib.request,os;"
        "urllib.request.urlretrieve('" + base + "/camevision-usb-sd.sh','/userdata/camevision-usb-sd.sh');"
        "urllib.request.urlretrieve('" + base + "/single_live.py','/userdata/single_live.py');"
        "urllib.request.urlretrieve('" + base + "/camevision-uvc-bridge.py','/userdata/camevision-uvc-bridge.py');"
        "print(os.path.getsize('/userdata/camevision-usb-sd.sh'),"
        "os.path.getsize('/userdata/single_live.py'),"
        "os.path.getsize('/userdata/camevision-uvc-bridge.py'))\"; "
        "sed -i 's/\\r$//' /userdata/camevision-usb-sd.sh /userdata/single_live.py /userdata/camevision-uvc-bridge.py; "
        "chmod 755 /userdata/camevision-usb-sd.sh; "
        "python3 -c \"import os,signal\n"
        "for p in os.listdir('/proc'):\n"
        "    if not p.isdigit():\n"
        "        continue\n"
        "    try:\n"
        "        d=open('/proc/'+p+'/cmdline','rb').read()\n"
        "    except OSError:\n"
        "        continue\n"
        "    if b'camevision-usb-sd.sh' in d or b'single_live.py' in d or b'camevision-uvc-bridge.py' in d:\n"
        "        os.kill(int(p),15)\n"
        "\"; "
        "sleep 1; "
        "printf '' > /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "sync; umount /mnt/sdcard; "
        "echo /dev/mmcblk1 > /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "setsid /bin/sh /userdata/camevision-usb-sd.sh </dev/null >>/userdata/cv-usb-sd.log 2>&1 & "
        "setsid /usr/bin/python3 /userdata/single_live.py </dev/null >>/userdata/single-live.log 2>&1 & "
        "echo $! >/tmp/single-live.pid; "
        "rm -f /tmp/camevision-uvc-ctl.json; "
        "setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 & "
        "sleep 2; "
        "echo LUN; cat /sys/kernel/config/usb_gadget/rockchip/functions/mass_storage.0/lun.0/file; "
        "echo MNT; grep sdcard /proc/mounts || echo none; "
        "echo CTL; cat /tmp/camevision-uvc-ctl.json; "
        "echo PS; ps | grep -E 'single_live|uvc-bridge|usb-sd|camevision_agent|bluetoothd' | grep -v grep"
    )
    print(cv_tn.run(cmd, wait=14.0))
    httpd.shutdown()


if __name__ == "__main__":
    main()
