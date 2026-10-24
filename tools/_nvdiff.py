#!/usr/bin/env python3
from pathlib import Path
fw = Path(__file__).resolve().parents[1] / "restore/release-1.1-mono-mira220-20261023/overlay/swt6621_fw"
a = (fw / "SWT6621S_NV_SDIO_ALONE.bin").read_bytes()
s = (fw / "SWT6621S_NV_SDIO_SHARE.bin").read_bytes()
print("len", len(a), len(s), "same", a == s)
for i, (x, y) in enumerate(zip(a, s)):
    if x != y:
        print(f"  off {i:3d} alone={x:02x} share={y:02x}")
