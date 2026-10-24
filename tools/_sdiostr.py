#!/usr/bin/env python3
from pathlib import Path

ko = Path(__file__).resolve().parents[1] / "restore/release-1.1-mono-mira220-20261023/overlay/swt6621-rt52/skw_sdio_lite.ko"
data = ko.read_bytes()
cur = b""
seen = []
keys = (b"sv61", b"cfg", b".bin", b".nv", b"bt", b"bind", b"SHARE", b"ALONE", b"swt6621", b"firmware")
for c in data:
    if 32 <= c < 127:
        cur += bytes([c])
    else:
        if len(cur) >= 6:
            low = cur.lower()
            if any(k.lower() in low for k in keys):
                s = cur.decode()
                if s not in seen:
                    seen.append(s)
        cur = b""
for s in seen:
    print(s)
