#!/usr/bin/env python3
from pathlib import Path

ko = Path(__file__).resolve().parents[1] / "restore/release-1.1-mono-mira220-20261023/overlay/swt6621-rt52/skw_sdio_lite.ko"
data = ko.read_bytes()
# print strings containing path-like or ant/share/alone
cur = b""
seen = []
for c in data:
    if 32 <= c < 127:
        cur += bytes([c])
    else:
        if len(cur) >= 4:
            s = cur.decode()
            low = s.lower()
            if any(k in low for k in ("ant", "share", "alone", "/data", "/lib", "/etc", "nv", "cfg", "proc")):
                if s not in seen:
                    seen.append(s)
        cur = b""
for s in seen:
    print(s)
