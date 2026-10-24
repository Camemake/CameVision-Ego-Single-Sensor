#!/usr/bin/env python3
"""Match CameVisionMono_OV V0.3 Wi-Fi pads on the Mono AM boot FIT.

Schematic WIFI_RST is GPIO0_A0 (AM13) into Q1 BSS84, not GPIO3_B2.
HOST_WAKE is GPIO3_B6, INT GPIO3_B7. Do not map Single GPIO2_A4/A5
(those are SDMMC0). Leave USB and the MIRA220 camera graph alone.
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dtb_decompile import Fdt, Node, build, printable_strings  # noqa: E402
from patch_boot_usb import (  # noqa: E402
    find,
    patch_resource_copy,
    prop_offsets,
    read_mem_rsvmap,
    serialize,
    set_prop,
)

GPIO0 = 0x95
GPIO3 = 0xB9
PCFG_PULL_NONE = 0xEC
PCFG_OUT_HIGH = 0xF7
PCFG_PULL_UP = 0xEE
MODULE = b"camevision-mira220"


def set_cells(node: Node, name: str, cells: list[int]) -> None:
    raw = struct.pack(f">{len(cells)}I", *cells)
    for i, (k, v) in enumerate(node.props):
        if k == name:
            old = " ".join(f"{c:#x}" for c in struct.unpack(f">{len(v)//4}I", v)) if v else ""
            node.props[i] = (name, raw)
            print(f"  {node.path()}: {name} <{old}> -> <{' '.join(f'{c:#x}' for c in cells)}>")
            return
    node.props.append((name, raw))
    print(f"  {node.path()}: {name} added <{' '.join(f'{c:#x}' for c in cells)}>")


def patch(root: Node) -> None:
    # CameVisionMono_OV V0.3 / Ego AM V0.3 sheet WiFi_BT:
    # RST GPIO0_A0 AM13, HOST_WAKE GPIO3_B6, INT GPIO3_B7.
    set_cells(find(root, "/sdio-pwrseq"), "reset-gpios", [GPIO0, 0, 0])
    set_cells(find(root, "/pinctrl/sdio-pwrseq/wifi-enable-h"), "rockchip,pins", [0, 0, 0, PCFG_PULL_NONE])
    set_cells(find(root, "/pinctrl/wireless-wlan/wifi-soc-pwctl"), "rockchip,pins", [3, 14, 0, PCFG_OUT_HIGH])
    set_cells(find(root, "/pinctrl/wireless-wlan/wifi-wake-host"), "rockchip,pins", [3, 15, 0, PCFG_PULL_UP])
    set_cells(find(root, "/wireless-wlan"), "WIFI,host_wake_irq", [GPIO3, 15, 0])


def verify(dtb: bytes) -> None:
    tree = build(Fdt(dtb))
    rst = struct.unpack(">3I", find(tree, "/sdio-pwrseq").get("reset-gpios"))
    if rst != (GPIO0, 0, 0):
        raise SystemExit(f"reset-gpios {rst}")
    en = struct.unpack(">4I", find(tree, "/pinctrl/sdio-pwrseq/wifi-enable-h").get("rockchip,pins"))
    if en != (0, 0, 0, PCFG_PULL_NONE):
        raise SystemExit(f"wifi-enable-h {en}")
    pins = struct.unpack(">4I", find(tree, "/pinctrl/wireless-wlan/wifi-soc-pwctl").get("rockchip,pins"))
    if pins != (3, 14, 0, PCFG_OUT_HIGH):
        raise SystemExit(f"pwctl pins {pins}")
    wake = struct.unpack(">4I", find(tree, "/pinctrl/wireless-wlan/wifi-wake-host").get("rockchip,pins"))
    if wake != (3, 15, 0, PCFG_PULL_UP):
        raise SystemExit(f"wake pins {wake}")
    wake_irq = struct.unpack(">3I", find(tree, "/wireless-wlan").get("WIFI,host_wake_irq"))
    if wake_irq != (GPIO3, 15, 0):
        raise SystemExit(f"wake irq {wake_irq}")
    usb = find(tree, "/usb@21500000")
    if printable_strings(usb.get("dr_mode")) != ["peripheral"]:
        raise SystemExit("USB dr_mode lost")
    if printable_strings(usb.get("maximum-speed")) != ["high-speed"]:
        raise SystemExit("USB speed lost")
    if MODULE not in dtb:
        raise SystemExit("MIRA220 module name lost")
    print("verify ok: RST GPIO0_A0, wake B6/B7, USB HS")


def main() -> int:
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src
    data = bytearray(src.read_bytes())
    fit = Fdt(bytes(data))
    fit_root = build(fit)
    offsets = prop_offsets(fit)
    img = find(fit_root, "/images/fdt")
    pos = struct.unpack(">I", img.get("data-position"))[0]
    size = struct.unpack(">I", img.get("data-size"))[0]
    next_pos = len(data)
    for n in fit_root.walk():
        p = n.get("data-position")
        if p is None:
            continue
        other = struct.unpack(">I", p)[0]
        if pos < other < next_pos:
            next_pos = other
    slot = next_pos - pos
    print(f"fdt at {pos:#x} size {size}, slot {slot}")

    old_hash = None
    for c in img.children:
        if printable_strings(c.get("algo") or b"") == ["sha256"]:
            old_hash = c.get("value")
    old = bytes(data[pos : pos + size])
    if old_hash and hashlib.sha256(old).digest() != old_hash:
        raise SystemExit("stored fdt hash mismatch")

    dtb = Fdt(old)
    root = build(dtb)
    print("edits:")
    patch(root)
    new_dtb = serialize(root, read_mem_rsvmap(dtb), dtb.boot_cpuid_phys)
    print(f"new fdt {len(new_dtb)} (was {size}, slot {slot})")
    if len(new_dtb) > slot:
        raise SystemExit(f"DTB {len(new_dtb) - slot} bytes too big")
    verify(new_dtb)

    data[pos:next_pos] = new_dtb + b"\x00" * (slot - len(new_dtb))
    if len(new_dtb) != size:
        off, plen = offsets[("/images/fdt", "data-size")]
        if plen != 4:
            raise SystemExit("data-size is not a cell")
        struct.pack_into(">I", data, off, len(new_dtb))
        print(f"FIT data-size {size} -> {len(new_dtb)}")
    new_hash = hashlib.sha256(new_dtb).digest()
    hoff, _ = offsets[("/images/fdt/hash", "value")]
    data[hoff : hoff + 32] = new_hash
    print(f"FIT fdt hash {old_hash.hex()[:16] if old_hash else ''}... -> {new_hash.hex()[:16]}...")
    patch_resource_copy(data, fit_root, offsets, new_dtb)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(data))
    print(f"wrote {dst} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
