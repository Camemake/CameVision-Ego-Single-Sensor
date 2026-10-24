#!/usr/bin/env python3
from pathlib import Path

fw = Path(__file__).resolve().parents[1] / "restore/release-1.1-mono-mira220-20261023/overlay/swt6621_fw"
for p in sorted(fw.iterdir()):
    b = p.read_bytes()
    print(f"{p.name:40s} {len(b):6d} {b[:24].hex()}")

ko = Path(__file__).resolve().parents[1] / "restore/release-1.1-mono-mira220-20261023/overlay/swt6621-rt52/swt6621s_wifi.ko"
data = ko.read_bytes()
cur = b""
seen = []
for c in data:
    if 32 <= c < 127:
        cur += bytes([c])
    else:
        if len(cur) >= 8:
            low = cur.lower()
            if any(k in low for k in (b"nv", b"sv61", b"swt6621", b"seek", b"share", b"alone", b".bin")):
                s = cur.decode()
                if s not in seen:
                    seen.append(s)
        cur = b""
print("WIFI STRINGS")
for s in seen:
    print(s)
