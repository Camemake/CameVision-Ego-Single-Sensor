#!/usr/bin/env python3
"""Advertise full UVC CT/PU controls in the compiled-in f_uvc defaults.

This Rockchip 6.1 gadget creates ConfigFS bmControls as read-only copies of
uvc_alloc_inst, so Windows usbvideo.sys only enables Brightness + Exposure.
Patch the packed immediates:

  camera  bmControls[0]  0x02 (AE only) -> 0xFF
  process bmControls     0x0001 (brightness) -> 0x17FF
    D0-D7  brightness, contrast, hue, sat, sharp, gamma, WB temp, WB comp
    D8-D12 backlight, gain, power-line, (hue auto unused), WB temp auto

Usage:
    python tools/patch_boot_uvc_controls.py <boot.img> [out.img]
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dtb_decompile import Fdt, build, printable_strings  # noqa: E402
from kernel_strings import find_kernel, lz4_decompress  # noqa: E402
from patch_boot_usb import find, prop_offsets  # noqa: E402

# uvc_alloc_inst @ 0x4aab7c — verified against "UVC Camera" snprintf xref.
CT_OFF = 0x4AABF4
PU_OFF = 0x4AAC14


def _movz_x4_lsl48(imm16: int) -> bytes:
    return struct.pack("<I", 0xD2E00000 | ((imm16 & 0xFFFF) << 5) | 4)


def _movk_x4_lsl16(imm16: int) -> bytes:
    return struct.pack("<I", 0xF2A00000 | ((imm16 & 0xFFFF) << 5) | 4)


# movz x4, #0x203, lsl #48  (bControlSize=3, bmControls[0]=2)
# movz x4, #0xFF03, lsl #48 (bControlSize=3, bmControls[0]=0xFF)
# movk x4, #0x1, lsl #16    (PU bmControls 0x0001)
# movk x4, #0x17FF, lsl #16 (PU bmControls 0x17FF)
# Steal the SS color-matching pointer store (HS uses the FS copy) to
# ADD the camera-terminal byte1/byte2 bits: zoom, pantilt, roll, focus-auto, privacy.
CT_OLD = _movz_x4_lsl48(0x203)
CT_NEW = _movz_x4_lsl48(0xFF03)
PU_OLD = _movk_x4_lsl16(0x1)
PU_NEW = _movk_x4_lsl16(0x17FF)
ADD_OFF = 0x4AAC04
ADD_OLD = struct.pack("<I", 0xA91D7E60)  # stp x0, xzr, [x19, #464]
ADD_NEW = struct.pack("<I", 0x91000000 | (0x062A << 10) | (4 << 5) | 4)  # add x4, x4, #0x062A


def patch_kernel(raw: bytearray) -> None:
    done = (
        raw[CT_OFF : CT_OFF + 4] == CT_NEW
        and raw[PU_OFF : PU_OFF + 4] == PU_NEW
        and raw[ADD_OFF : ADD_OFF + 4] == ADD_NEW
    )
    if done:
        print("kernel UVC controls already patched")
        return
    if raw[CT_OFF : CT_OFF + 4] == CT_OLD:
        raw[CT_OFF : CT_OFF + 4] = CT_NEW
    elif raw[CT_OFF : CT_OFF + 4] != CT_NEW:
        raise SystemExit(f"CT site {raw[CT_OFF:CT_OFF+4].hex()}")
    if raw[PU_OFF : PU_OFF + 4] == PU_OLD:
        raw[PU_OFF : PU_OFF + 4] = PU_NEW
    elif raw[PU_OFF : PU_OFF + 4] != PU_NEW:
        raise SystemExit(f"PU site {raw[PU_OFF:PU_OFF+4].hex()}")
    if raw[ADD_OFF : ADD_OFF + 4] == ADD_OLD:
        raw[ADD_OFF : ADD_OFF + 4] = ADD_NEW
    elif raw[ADD_OFF : ADD_OFF + 4] != ADD_NEW:
        raise SystemExit(f"ADD site {raw[ADD_OFF:ADD_OFF+4].hex()} (want {ADD_OLD.hex()})")
    print(
        f"patched uvc_alloc_inst CT bm=0xFF/0x2A/0x06 @ {CT_OFF:#x}/{ADD_OFF:#x}, "
        f"PU bm=0x17FF @ {PU_OFF:#x}"
    )


def patch_fit(src: Path, dst: Path) -> None:
    data = bytearray(src.read_bytes())
    fit = Fdt(bytes(data))
    fit_root = build(fit)
    offsets = prop_offsets(fit)
    kern = find(fit_root, "/images/kernel")
    pos = struct.unpack(">I", kern.get("data-position"))[0]
    size = struct.unpack(">I", kern.get("data-size"))[0]
    next_pos = len(data)
    for n in fit_root.walk():
        p = n.get("data-position")
        if p is None:
            continue
        other = struct.unpack(">I", p)[0]
        if pos < other < next_pos:
            next_pos = other
    slot = next_pos - pos
    blob = bytes(data[pos : pos + size])
    raw = bytearray(lz4_decompress(blob))
    print(f"kernel at {pos:#x} lz4 {size} raw {len(raw)} slot {slot}")
    patch_kernel(raw)

    import lz4.frame

    new_blob = lz4.frame.compress(
        bytes(raw),
        compression_level=9,
        block_size=lz4.frame.BLOCKSIZE_MAX4MB,
        block_linked=False,
        content_checksum=True,
        store_size=False,
    )
    print(f"recompressed lz4 {size} -> {len(new_blob)}")
    if len(new_blob) > slot:
        raise SystemExit(f"kernel {len(new_blob) - slot} bytes too big for slot")
    check = bytearray(lz4_decompress(new_blob))
    if (
        check[CT_OFF : CT_OFF + 4] != CT_NEW
        or check[PU_OFF : PU_OFF + 4] != PU_NEW
        or check[ADD_OFF : ADD_OFF + 4] != ADD_NEW
    ):
        raise SystemExit("recompressed kernel lost UVC control patch")
    data[pos:next_pos] = new_blob + b"\x00" * (slot - len(new_blob))
    off, plen = offsets[("/images/kernel", "data-size")]
    if plen != 4:
        raise SystemExit("kernel data-size is not a cell")
    struct.pack_into(">I", data, off, len(new_blob))
    new_hash = hashlib.sha256(new_blob).digest()
    hoff, _ = offsets[("/images/kernel/hash", "value")]
    data[hoff : hoff + 32] = new_hash
    print(f"FIT kernel hash -> {new_hash.hex()[:16]}...")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(data))
    print(f"wrote {dst} ({len(data)} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: patch_boot_uvc_controls.py <boot.img> [out.img]")
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src
    patch_fit(src, dst)
