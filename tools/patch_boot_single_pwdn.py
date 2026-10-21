#!/usr/bin/env python3
"""Restore M1 CAM_PWDN polarity on a Single boot FIT.

The v5 patch set reset-gpios flags to GPIO_ACTIVE_HIGH (run = low). The M1
kernel and the SC233HGS on this board need GPIO_ACTIVE_LOW (run = high).
With the wrong flag the driver enables xvclk (clk_mipi0_out2io) then holds
CAM_PWDN low, chip-id NACKs, probe fails, and the clock is released.

Does not reserialize the DTB. Only the last cell of reset-gpios is flipped,
then FIT + resource hashes are recomputed.
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dtb_decompile import Fdt, build, printable_strings  # noqa: E402
from patch_boot_usb import find, patch_resource_copy, prop_offsets  # noqa: E402

SRC = Path(
    r"C:\Users\stefa\Desktop\CameVision Single"
    r"\restore\diag-adb-20260902\camevision_boot_diag_adb.img"
)
DST = Path(
    r"C:\Users\stefa\Desktop\CameVision Single"
    r"\restore\diag-adb-20260902\camevision_boot_diag_adb_m1pwdn.img"
)

# gpio4 pin 6, ACTIVE_HIGH -> ACTIVE_LOW
OLD = struct.pack(">3I", 0x9C, 6, 0)
NEW = struct.pack(">3I", 0x9C, 6, 1)


def patch_dtb(dtb: bytes) -> bytes:
    n = dtb.count(OLD)
    if n != 1:
        raise SystemExit(f"reset-gpios pattern count {n}, expected 1")
    return dtb.replace(OLD, NEW, 1)


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DST
    data = bytearray(src.read_bytes())
    fit = Fdt(bytes(data))
    fit_root = build(fit)
    offsets = prop_offsets(fit)
    img = find(fit_root, "/images/fdt")
    pos = struct.unpack(">I", img.get("data-position"))[0]
    size = struct.unpack(">I", img.get("data-size"))[0]
    old_hash = None
    for c in img.children:
        if printable_strings(c.get("algo") or b"") == ["sha256"]:
            old_hash = c.get("value")
    old = bytes(data[pos : pos + size])
    if hashlib.sha256(old).digest() != old_hash:
        raise SystemExit("stored fdt hash mismatch")

    new_dtb = patch_dtb(old)
    tree = build(Fdt(new_dtb))
    cam = find(tree, "/i2c@21120000/sc233hgs@30")
    rst = struct.unpack(">3I", cam.get("reset-gpios"))
    if rst != (0x9C, 6, 1):
        raise SystemExit(f"camera reset {rst}")
    print(f"  reset-gpios <0x9c 0x6 0x0> -> <0x9c 0x6 0x1> ACTIVE_LOW")

    data[pos : pos + size] = new_dtb
    new_hash = hashlib.sha256(new_dtb).digest()
    hoff, _ = offsets[("/images/fdt/hash", "value")]
    data[hoff : hoff + 32] = new_hash
    print(f"FIT fdt hash {old_hash.hex()[:16]}... -> {new_hash.hex()[:16]}...")
    patch_resource_copy(data, fit_root, offsets, new_dtb)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(data))
    print(f"wrote {dst} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
