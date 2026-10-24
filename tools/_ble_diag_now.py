#!/usr/bin/env python3
import cv_tn

print(
    cv_tn.run(
        "echo LOG; tail -60 /userdata/camevision-agent.log; "
        "echo ---REC; ls -l /tmp/camevision-record.on 2>/dev/null; "
        "echo ---SESS; ls -lt /userdata/sd/camevision /media/sd/camevision /mnt/sd/camevision 2>/dev/null | head -12; "
        "echo ---CONN; bluetoothctl devices Connected; "
        "echo ---HTTP; wget -q -O - http://127.0.0.1:8090/v1/status; echo",
        wait=8.0,
    )
)
