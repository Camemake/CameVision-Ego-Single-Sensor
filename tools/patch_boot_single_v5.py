#!/usr/bin/env python3
"""Patch the Wi-Fi/IMU boot DTB for MonoCamStack_Soc V5 + Power V3.

Adds GPIO enables for the camera LDOs on the power board and fixes CAM_PWDN
polarity. Does not touch USB or move the IMU (already on SPI1).

  PWR_EN_2.8V  GPIO0_B0  U3 LDLN025  +2.8V_AVDD
  PWR_EN_1.5V  GPIO0_B1  U4 MIC5317  +1.5V_DVDD
  CAM_PWDN     GPIO4_A6  reset-gpios ACTIVE_LOW (run = high), same as M1
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

SRC = Path(
    r"C:\Users\stefa\Desktop\CameVision Single"
    r"\restore\recovery-2-20260821-adb-stream\camevision_boot_wifi_imu.img"
)
DST = Path(
    r"C:\Users\stefa\Desktop\CameVision Single"
    r"\restore\recovery-2-20260821-adb-stream\camevision_boot_single_v5.img"
)

GPIO0 = 0x95  # /pinctrl/gpio@20600000
# GPIO0_B0 = 8, GPIO0_B1 = 9, GPIO_ACTIVE_HIGH = 0
PWR_EN_28 = [GPIO0, 8, 0]
PWR_EN_15 = [GPIO0, 9, 0]


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


def ensure_empty(node: Node, name: str) -> None:
    if node.get(name) is None:
        node.props.append((name, b""))
        print(f"  {node.path()}: {name} added (empty)")


def patch_board(root: Node) -> None:
    set_prop(root, "/", "model", b"CameVision Single\x00")
    set_prop(
        root,
        "/",
        "compatible",
        b"camemake,camevision-single\x00rockchip,rv1126b\x00",
    )

    avdd = find(root, "/sc233hgs-avdd")
    set_cells(avdd, "gpio", PWR_EN_28)
    ensure_empty(avdd, "enable-active-high")
    set_cells(avdd, "startup-delay-us", [20000])

    dvdd = find(root, "/sc233hgs-dvdd")
    set_cells(dvdd, "gpio", PWR_EN_15)
    ensure_empty(dvdd, "enable-active-high")
    set_cells(dvdd, "startup-delay-us", [20000])

    # M1 / live SC233HGS: CAM_PWDN is XSHUTDN, run = high = GPIO_ACTIVE_LOW.
    cam = find(root, "/i2c@21120000/sc233hgs@30")
    set_cells(cam, "reset-gpios", [0x9C, 6, 1])
    set_prop(root, "/i2c@21120000/sc233hgs@30", "rockchip,camera-module-facing", b"front\x00")
    set_prop(
        root,
        "/i2c@21120000/sc233hgs@30",
        "rockchip,camera-module-name",
        b"efference-sc233hgs\x00",
    )


def verify(dtb: bytes) -> None:
    tree = build(Fdt(dtb))
    if printable_strings(find(tree, "/").get("model")) != ["CameVision Single"]:
        raise SystemExit("model not updated")
    avdd = find(tree, "/sc233hgs-avdd")
    gpio = struct.unpack(">3I", avdd.get("gpio"))
    if gpio != tuple(PWR_EN_28):
        raise SystemExit(f"avdd gpio {gpio}")
    dvdd = find(tree, "/sc233hgs-dvdd")
    gpio = struct.unpack(">3I", dvdd.get("gpio"))
    if gpio != tuple(PWR_EN_15):
        raise SystemExit(f"dvdd gpio {gpio}")
    cam = find(tree, "/i2c@21120000/sc233hgs@30")
    rst = struct.unpack(">3I", cam.get("reset-gpios"))
    if rst != (0x9C, 6, 1):
        raise SystemExit(f"camera reset {rst}")
    wlan = find(tree, "/wireless-wlan")
    if printable_strings(wlan.get("wifi_chip_type")) != ["vs6621"]:
        raise SystemExit("wifi_chip_type lost")
    usb = find(tree, "/usb@21500000")
    if printable_strings(usb.get("dr_mode")) != ["peripheral"]:
        raise SystemExit("USB dr_mode lost")
    print("verify ok: Single model, camera LDO GPIOs, PWDN polarity, VS6621, USB")


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
    if hashlib.sha256(old).digest() != old_hash:
        raise SystemExit("stored fdt hash mismatch")

    dtb = Fdt(old)
    root = build(dtb)
    print("edits:")
    patch_board(root)
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
    print(f"FIT fdt hash {old_hash.hex()[:16]}... -> {new_hash.hex()[:16]}...")
    patch_resource_copy(data, fit_root, offsets, new_dtb)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(data))
    print(f"wrote {dst} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
