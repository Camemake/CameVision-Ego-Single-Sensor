#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "python3 -c \"import os,signal\n"
        "seen=0\n"
        "for p in os.listdir('/proc'):\n"
        "    if not p.isdigit():\n"
        "        continue\n"
        "    try:\n"
        "        d=open('/proc/'+p+'/cmdline','rb').read()\n"
        "    except OSError:\n"
        "        continue\n"
        "    if b'camevision-usb-sd.sh' in d:\n"
        "        seen += 1\n"
        "        if seen > 1:\n"
        "            os.kill(int(p),15)\n"
        "print('usb-sd', seen)\n"
        "\"; ps | grep usb-sd | grep -v grep",
        wait=4.0,
    )
)
