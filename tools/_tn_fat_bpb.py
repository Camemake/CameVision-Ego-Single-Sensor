#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "wget -q -O /tmp/_fat_bpb.py http://192.168.1.44:18767/_fat_bpb.py; "
        "python3 /tmp/_fat_bpb.py; "
        "wget -q -O - http://127.0.0.1:8090/v1/status; echo; "
        "echo BPB_DONE",
        wait=8,
    )
)
