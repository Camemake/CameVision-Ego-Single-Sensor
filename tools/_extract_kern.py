#!/usr/bin/env python3
"""Extract and decompress the lz4 kernel from the Mono boot FIT."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from kernel_strings import find_kernel, lz4_decompress

BOOT = Path(__file__).resolve().parents[1] / (
    "restore/release-1.1-mono-mira220-20261023/camevision_boot_mono_wifi.pre-sd.img"
)
OUT = Path(__file__).resolve().parent / "_kernel.bin"

data = BOOT.read_bytes()
pos, size, comp = find_kernel(data)
print(f"kernel at {pos:#x} size {size} compression {comp}")
blob = data[pos : pos + size]
print(f"first {blob[:8].hex()}")
raw = lz4_decompress(blob) if comp == "lz4" else blob
print(f"decompressed {len(raw)}")
OUT.write_bytes(raw)
print(f"wrote {OUT}")
