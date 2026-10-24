#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "kill $(ps | awk '/http.server 8092/ && !/awk/ {print $1}') 2>/dev/null; "
        "cd /tmp; setsid python3 -m http.server 8092 </dev/null >/dev/null 2>&1 & "
        "sleep 0.3; echo SERVE; ls -l /tmp/camevision-live.jpg; "
        "find / -name 'video.mp4' 2>/dev/null | head; "
        "find / -name '20261023T042048Z' -o -name 'imu0.csv' 2>/dev/null | head; "
        "ls -la /userdata/camevision 2>&1 | head",
        wait=8.0,
    )
)
