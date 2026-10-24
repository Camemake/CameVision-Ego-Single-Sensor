#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "cd /userdata; wget -q -O camevision-uvc-bridge.py http://192.168.1.44:18770/camevision-uvc-bridge.py; "
        "sed -i 's/\\r$//' camevision-uvc-bridge.py; "
        "kill $(ps | awk '/camevision-uvc-bridge.py/ && !/awk/ {print $1}') 2>/dev/null; "
        "rm -f /tmp/camevision-uvc-ctl.json; "
        "setsid /usr/bin/python3 /userdata/camevision-uvc-bridge.py </dev/null >>/userdata/cv-uvc-bridge.log 2>&1 & "
        "sleep 1; cat /tmp/camevision-uvc-ctl.json; "
        "tail -5 /userdata/single-live.log; "
        "ps | grep -E 'uvc-bridge|single_live' | grep -v grep",
        wait=8.0,
    )
)
