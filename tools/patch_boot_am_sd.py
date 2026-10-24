#!/usr/bin/env python3
"""Enable microSD on the Mono AM boot FIT at 3.3 V card I/O.

The live DTB already has vmmc=vcc3v3_sd (node still named vcc1v8-sd) and
vqmmc=vcc3v3_sys, both 3.3 V. sdmmc0 is left disabled, so no mmc1 host
appears. Do not use vcc_1v8 here: SD init is 3.3 V. Do not mux SDMMC0_DET
(GPIO0_A5, green LED) or SDMMC0_PWREN (GPIO0_B2, CAM0 DVDD). Card detect
GPIO3_B3 is not trusted, so broken-cd polls the inserted card.

    python tools/patch_boot_am_sd.py restore/release-1.1-mono-mira220-20261023/camevision_boot_mono_wifi.img
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dtb_decompile import Fdt, Node, build, printable_strings  # noqa: E402
from kernel_strings import lz4_decompress  # noqa: E402
from patch_boot_usb import (  # noqa: E402
    del_prop,
    find,
    patch_resource_copy,
    prop_offsets,
    read_mem_rsvmap,
    serialize,
    set_prop,
)

# mmc_sd_get_cid: cbnz after mmc_send_if_cond skips SD_OCR_CCS (HCS).
# CMD8 CRC-fails on this slot; without HCS the card stays 2 GB SDSC.
HCS_OFF = 0x5A756C
HCS_OLD = bytes.fromhex("40000035")  # cbnz w0, +8
HCS_NEW = bytes.fromhex("1f2003d5")  # nop — still send CMD8, always set HCS
# USRID 0x20230001 programs TIMING_CON, but set_ios skips that path when
# ciu-sample / ciu-drive clocks are missing. RV1126B has no those clocks.
SAMP_SKIP_OFF = 0x5B7318
SAMP_SKIP_OLD = bytes.fromhex("c8010054")  # b.hi skip sample phase
DRV_SKIP_OFF = 0x5B7358
DRV_SKIP_OLD = bytes.fromhex("68020054")  # b.hi skip drive phase
NOP = bytes.fromhex("1f2003d5")
# CSD v1 always takes the flag-orr at 0x5A777C (was only if WP bit).
# Change that orr from MMC_STATE_READONLY (#2) to MMC_STATE_BLOCKADDR (#4)
# so CMD17 uses LBA like the Windows reader. No execute_tuning cave.
V1_TBZ_OFF = 0x5A7778
V1_TBZ_OLD = bytes.fromhex("05076836")  # tbz w5,#13, join
V1_TBZ_NEW = bytes.fromhex("01000014")  # b +4 → always orr flags
V1_ORR_OFF = 0x5A7780
V1_ORR_OLD = bytes.fromhex("21001f32")  # orr w1,w1,#2
V1_ORR_NEW = bytes.fromhex("21001e32")  # orr w1,w1,#4
# Windows D: 15634268160 bytes = 30535680 512-byte sectors.
# v1 CSD READ_BL_LEN=10, so kernel does sectors = csd.capacity << 1.
# Store 15267840 to publish 30535680.
V1_CAP_OFF = 0x5A771C
V1_CAP_OLD = bytes.fromhex("840400118420c51a442400b9")  # add; lsl; str capacity
V1_CAP_NEW = bytes.fromhex("04009f52041da072442400b9")  # mov w4,#0xF800; movk #0xE8,lsl16; str

MODULE = b"camevision-mira220"
# 3.3 V I/O, no UHS. 4-bit / 25 MHz HS still CRC-fails data and the
# card still answers as 2 GB SDSC, so stay on the 1-bit identify path
# that can actually mount the FAT volume.
HS_HZ = 12_500_000
GPIO0 = 0x95


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


def u32(node: Node, name: str) -> int:
    raw = node.get(name)
    if raw is None or len(raw) < 4:
        raise SystemExit(f"{node.path()} missing {name}")
    return struct.unpack(">I", raw[:4])[0]


def phandle_node(root: Node, ph: int) -> Node:
    for n in root.walk():
        raw = n.get("phandle")
        if raw and struct.unpack(">I", raw)[0] == ph:
            return n
    raise SystemExit(f"phandle {ph:#x} not found")


def volt(node: Node) -> int:
    raw = node.get("regulator-min-microvolt")
    if raw is None:
        raise SystemExit(f"{node.path()} has no regulator-min-microvolt")
    return struct.unpack(">I", raw)[0]


def patch(root: Node) -> None:
    mmc = find(root, "/mmc@21d60000")
    set_prop(root, "/mmc@21d60000", "status", b"okay\x00")
    set_prop(root, "/mmc@21d60000", "broken-cd", b"")
    set_prop(root, "/mmc@21d60000", "no-1-8-v", b"")
    # Bind the rk3568 path so parse_dt treats this as an internal-phase host.
    # Same length as rockchip,rv1126b-dw-mshc; rk3288 stays as fallback.
    compat = mmc.get("compatible") or b""
    new_compat = compat.replace(b"rockchip,rv1126b-dw-mshc\x00", b"rockchip,rk3568-dw-mshc\x00")
    if new_compat == compat:
        raise SystemExit("sdmmc0 compatible did not contain rv1126b-dw-mshc")
    set_prop(root, "/mmc@21d60000", "compatible", new_compat)
    del_prop(root, "/mmc@21d60000", "fifo-mode")
    del_prop(root, "/mmc@21d60000", "cap-sd-highspeed")
    del_prop(root, "/mmc@21d60000", "cd-gpios")
    set_cells(mmc, "max-frequency", [HS_HZ])
    set_cells(mmc, "bus-width", [1])
    # String already exists on eMMC. Phase 0 is why CMD8 CRC-fails and
    # the card falls back to the 2 GB SDSC identity Windows does not use.
    set_cells(mmc, "rockchip,default-sample-phase", [90])
    pins = mmc.get("pinctrl-0")
    if not pins or len(pins) < 12:
        raise SystemExit("sdmmc0 pinctrl-0 missing clk/cmd/bus4")
    cells = list(struct.unpack(f">{len(pins)//4}I", pins))
    set_cells(mmc, "pinctrl-0", cells[:3])
    for banned in ("sd-uhs-sdr104", "sd-uhs-sdr50", "sd-uhs-ddr50", "sd-uhs-sdr25"):
        del_prop(root, "/mmc@21d60000", banned)
    # Stock sdmmc0 bias. 0xf3 did not help CMD8.
    pull5 = 0xF2
    for path in (
        "/pinctrl/sdmmc0/sdmmc0-clk-pins",
        "/pinctrl/sdmmc0/sdmmc0-cmd-pins",
        "/pinctrl/sdmmc0/sdmmc0-bus4-pins",
    ):
        node = find(root, path)
        raw = node.get("rockchip,pins")
        cells = list(struct.unpack(f">{len(raw)//4}I", raw))
        for i in range(3, len(cells), 4):
            cells[i] = pull5
        set_cells(node, "rockchip,pins", cells)


def verify(dtb: bytes) -> None:
    tree = build(Fdt(dtb))
    mmc = find(tree, "/mmc@21d60000")
    if printable_strings(mmc.get("status")) != ["okay"]:
        raise SystemExit("sdmmc0 status is not okay")
    if mmc.get("broken-cd") is None:
        raise SystemExit("broken-cd missing")
    if mmc.get("cd-gpios") is not None:
        raise SystemExit("cd-gpios still present")
    if u32(mmc, "max-frequency") != HS_HZ:
        raise SystemExit(f"max-frequency {u32(mmc, 'max-frequency')}")
    if mmc.get("no-1-8-v") is None:
        raise SystemExit("no-1-8-v missing")
    if u32(mmc, "rockchip,default-sample-phase") != 90:
        raise SystemExit("sample-phase is not 90")
    if b"rockchip,rk3568-dw-mshc" not in (mmc.get("compatible") or b""):
        raise SystemExit("sdmmc0 compatible is not rk3568-dw-mshc")
    if mmc.get("cap-sd-highspeed") is not None:
        raise SystemExit("cap-sd-highspeed would force 4-bit HS CRC errors")
    if u32(mmc, "bus-width") != 1:
        raise SystemExit("bus-width is not 1")
    for banned in ("sd-uhs-sdr104", "sd-uhs-sdr50", "sd-uhs-ddr50"):
        if mmc.get(banned) is not None:
            raise SystemExit(f"{banned} would switch I/O to 1.8 V")
    vmmc = volt(phandle_node(tree, u32(mmc, "vmmc-supply")))
    vqmmc = volt(phandle_node(tree, u32(mmc, "vqmmc-supply")))
    if vmmc != 3_300_000 or vqmmc != 3_300_000:
        raise SystemExit(f"SD voltage vmmc={vmmc} vqmmc={vqmmc} (need 3.3 V / 3.3 V)")
    usb = find(tree, "/usb@21500000")
    if printable_strings(usb.get("dr_mode")) != ["peripheral"]:
        raise SystemExit("USB dr_mode lost")
    if printable_strings(usb.get("maximum-speed")) != ["high-speed"]:
        raise SystemExit("USB speed lost")
    rst = struct.unpack(">3I", find(tree, "/sdio-pwrseq").get("reset-gpios"))
    if rst[1] != 0:
        raise SystemExit(f"WIFI_RST pin {rst} (want GPIO0_A0)")
    if MODULE not in dtb:
        raise SystemExit("MIRA220 module name lost")
    print("verify ok: sdmmc0 3.3 V / 3.3 V, broken-cd, USB HS, WIFI_RST A0")


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
    patch_kernel_hcs(data, fit_root, offsets)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(bytes(data))
    print(f"wrote {dst} ({len(data)} bytes)")
    return 0


def patch_kernel_hcs(data: bytearray, fit_root: Node, offsets: dict) -> None:
    import lz4.frame

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
    if raw[HCS_OFF : HCS_OFF + 4] != HCS_OLD:
        raise SystemExit(f"HCS check {raw[HCS_OFF:HCS_OFF+4].hex()} (want {HCS_OLD.hex()})")
    if raw[SAMP_SKIP_OFF : SAMP_SKIP_OFF + 4] != SAMP_SKIP_OLD:
        raise SystemExit(f"sample skip {raw[SAMP_SKIP_OFF:SAMP_SKIP_OFF+4].hex()}")
    if raw[DRV_SKIP_OFF : DRV_SKIP_OFF + 4] != DRV_SKIP_OLD:
        raise SystemExit(f"drive skip {raw[DRV_SKIP_OFF:DRV_SKIP_OFF+4].hex()}")
    raw[HCS_OFF : HCS_OFF + 4] = HCS_NEW
    raw[SAMP_SKIP_OFF : SAMP_SKIP_OFF + 4] = NOP
    raw[DRV_SKIP_OFF : DRV_SKIP_OFF + 4] = NOP
    # v1 blockaddr + 16 GB CSD stay off for this write. CMD24 does not
    # persist in that mode; format the FAT32 volume from the working host.
    new_blob = lz4.frame.compress(
        bytes(raw),
        compression_level=9,
        block_size=lz4.frame.BLOCKSIZE_MAX4MB,
        block_linked=False,
        content_checksum=True,
        store_size=False,
    )
    print(f"kernel HCS+phase nops, lz4 {size} -> {len(new_blob)} slot {slot}")
    if len(new_blob) > slot:
        raise SystemExit(f"kernel {len(new_blob) - slot} bytes too big")
    check = lz4_decompress(new_blob)
    if check[HCS_OFF : HCS_OFF + 4] != HCS_NEW:
        raise SystemExit("recompressed kernel lost HCS patch")
    if check[SAMP_SKIP_OFF : SAMP_SKIP_OFF + 4] != NOP:
        raise SystemExit("recompressed kernel lost sample-phase nop")
    if check[DRV_SKIP_OFF : DRV_SKIP_OFF + 4] != NOP:
        raise SystemExit("recompressed kernel lost drive-phase nop")
    data[pos:next_pos] = new_blob + b"\x00" * (slot - len(new_blob))
    off, plen = offsets[("/images/kernel", "data-size")]
    if plen != 4:
        raise SystemExit("kernel data-size is not a cell")
    struct.pack_into(">I", data, off, len(new_blob))
    new_hash = hashlib.sha256(new_blob).digest()
    hoff, _ = offsets[("/images/kernel/hash", "value")]
    data[hoff : hoff + 32] = new_hash
    print(f"FIT kernel hash -> {new_hash.hex()[:16]}...")


if __name__ == "__main__":
    raise SystemExit(main())
