#!/usr/bin/env python3
"""Store the working CameVision Mono / MIRA220 kit in restore/.

Does not write into the SC233HGS Single restore. Ego stays a sibling
source for the shared RV1126B images and the current AM boot FIT.
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from cv_single_paths import first_file, first_dir, overlay_dir, repo_root
from cv_single_paths_am import (
    AM_RELEASE,
    BOOT_NAME,
    EGO_AM_RELEASE,
    IQ_NAME_AM,
    MODULE,
    boot_ok_am,
)

ROOT = repo_root()
REL = ROOT / "restore" / AM_RELEASE
EGO = ROOT.parent / "CameVision Ego" / "restore" / EGO_AM_RELEASE
TOOLS = ROOT / "tools"

SHARED_IMGS = (
    "rv1126b_spl_loader_k4a8g.bin",
    "env.img",
    "idblock.img",
    "uboot.img",
    "oem_noko.img",
    "rootfs_bootstable.img",
)

AM_KOS = (
    "mira220.ko",
    "miralink.ko",
    "ciflate.ko",
    "clkgo.ko",
    "mfix4.ko",
    "mstart.ko",
)


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  {src.name} -> {dst}", flush=True)


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    n = sum(1 for p in dst.rglob("*") if p.is_file())
    print(f"  {src} -> {dst} ({n} files)", flush=True)


def write_docs(rel: Path) -> None:
    (rel / "SENSOR").write_text("MIRA220\n", encoding="ascii")
    (rel / "BOARD").write_text("MONO\n", encoding="ascii")
    (rel / "VERSION").write_text("1.0-mono-mira220\n", encoding="ascii")
    (rel / "RELEASE.md").write_text(
        """# CameVision Mono · MIRA220 · 1.0 — 14 October 2026

This folder is the **Mono / MIRA220** kit. It is **not** the SC233HGS
Single kit (`restore/known-good-20260903-single-camera`) and **not** Ego
stereo. Do not flash one onto the other.

Hardware: CameVisionMono_OV V0.3, one AMS MIRA220 (1600×1400 RAW10, GRBG),
one LSM6 on SPI0. Live view is 1400×1600 after 90° CCW. USB stays **ADB**.

```
python tools/cv_single_flash.py --package camevision-mono
python tools/cv_single_overlay_deploy_am.py
```

| Partition | Image |
|---|---|
| env / idblock / uboot | same RV1126B SPL set as Ego AM |
| boot | `camevision_boot_mono.img` (MIRA220 DTB; CAM1 unused) |
| userdata | Mono overlay (CIF CAM0, mira modules, MIRA220 IQ) |
| oem / rootfs | CameVision `oem_noko.img` / `rootfs_bootstable.img` |

Overlay:

- Live page `:8081` — CIF RAW10, Ego AM color path, 1400×1600
- IMU HUD `:8083` — IMU0 only
- `S10mira220` — CAM0 power + mira220 + ciflate + miralink
- IQ `mira220_camevision-mira220_default.json`
- Color decoder `libsingle_color.so` (`ego_raw10_color_nv12`)
- Exposure 3600, vblank 2695, VSTART 0 (re-applied after stream-on)

## Do not

- Flash this kit onto a SC233HGS board
- Use `tools/cv_single_flash.py` without `--package camevision-mono`
- Ship `ego_stereo.py` or start a second camera
- Switch USB to a webcam gadget
""",
        encoding="utf-8",
    )
    (rel / "FLASH.md").write_text(
        """# CameVision Mono / MIRA220 · Maskrom flash

Empty Mono AM board. USB stays **ADB**.

```
python tools/cv_single_flash.py --package camevision-mono
```

Board already running: `restore-mono.ps1` or
`python tools/cv_single_overlay_deploy_am.py`.
""",
        encoding="utf-8",
    )
    (rel / "restore-mono.ps1").write_text(
        """# Push CameVision Mono / MIRA220 overlay. USB stays ADB.
$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
python "$root\\tools\\cv_single_overlay_deploy_am.py"
""",
        encoding="utf-8",
    )


def stage_overlay(stg: Path) -> None:
    if stg.exists():
        shutil.rmtree(stg)
    stg.mkdir(parents=True)
    ov = overlay_dir()
    cur = ROOT / "restore" / "known-good-20260903-single-camera"
    mapping = {
        "single_live.py": TOOLS / "single_live.py",
        "single_imu_hud.py": TOOLS / "single_imu_hud.py",
        "camevision_agent.py": TOOLS / "camevision_agent.py",
        "camevision_ble.py": TOOLS / "camevision_ble.py",
        "libsingle_color.so": TOOLS / "libsingle_color.so",
        "camevision-single.sh": TOOLS / "camevision-single.sh",
        "S99camevision-single": TOOLS / "S99camevision-single",
        "S10mira220": TOOLS / "S10mira220",
        "S11hwclock": TOOLS / "S11hwclock",
        "camemake-logo.png": TOOLS / "camemake-logo.png",
        "camevision-wifi.sh": first_file(TOOLS / "camevision-wifi.sh", ov / "camevision-wifi.sh"),
        "wpa_camevision.conf": first_file(TOOLS / "wpa_camevision.conf", ov / "wpa_camevision.conf"),
        "camevision-hw.sh": first_file(TOOLS / "camevision-hw.sh", ov / "camevision-hw.sh"),
        "camevision-led.sh": first_file(TOOLS / "camevision-led.sh", ov / "camevision-led.sh"),
        "S50usbdevice": first_file(ov / "S50usbdevice", cur / "overlay" / "S50usbdevice"),
        "S99camevision": TOOLS / "S99camevision-single",
    }
    for name, src in mapping.items():
        if src is not None and Path(src).is_file():
            _copy(Path(src), stg / name)
    (stg / "camevision-am.on").write_text("am\n", encoding="ascii")
    iq = TOOLS / "iqfiles" / IQ_NAME_AM
    if not iq.is_file():
        raise SystemExit(f"missing MIRA220 IQ {iq}")
    _copy(iq, stg / "iqfiles" / iq.name)
    so = TOOLS / "libsingle_color.so"
    if not so.is_file():
        raise SystemExit("missing tools/libsingle_color.so")
    for ko in AM_KOS:
        src = first_file(TOOLS / "am-modules" / ko, EGO / "overlay" / "modules" / ko)
        if src is None:
            raise SystemExit(f"missing module {ko}")
        _copy(src, stg / "modules" / ko)
    kmpp = first_file(
        ov / "kmpp-rt52.ko",
        cur / "overlay" / "kmpp-rt52.ko",
        ROOT / "restore" / "recovery-3-20260822-uvc-wifi-rkaiq" / "overlay" / "kmpp-rt52.ko",
    )
    if kmpp is not None:
        _copy(kmpp, stg / "kmpp-rt52.ko")
    for folder in ("swt6621-rt52", "swt6621_fw"):
        src = first_dir(ov / folder, cur / "overlay" / folder)
        if src is not None:
            _copy_tree(src, stg / folder)


def sha256sums(rel: Path) -> None:
    lines = []
    for p in sorted(rel.rglob("*")):
        if not p.is_file() or p.name == "SHA256SUMS.txt":
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{digest}  {p.relative_to(rel).as_posix()}\n")
    (rel / "SHA256SUMS.txt").write_text("".join(lines), encoding="ascii")
    print(f"SHA256SUMS {len(lines)} files", flush=True)


def verify_kit(rel: Path) -> None:
    if (rel / "SENSOR").read_text(encoding="ascii").strip() != "MIRA220":
        raise SystemExit("MONO SENSOR is not MIRA220")
    boot = rel / BOOT_NAME
    raw = boot.read_bytes()
    if not boot_ok_am(raw):
        raise SystemExit("Mono boot FIT failed MIRA220 check")
    ov = rel / "overlay"
    if not (ov / "iqfiles" / IQ_NAME_AM).is_file():
        raise SystemExit("Mono overlay missing MIRA220 IQ")
    if not (ov / "libsingle_color.so").is_file():
        raise SystemExit("Mono overlay missing libsingle_color.so")
    if not (ov / "single_live.py").is_file():
        raise SystemExit("Mono overlay missing single_live.py")
    if (ov / "ego_stereo.py").is_file():
        raise SystemExit("Mono overlay must not ship ego_stereo.py")
    for ko in AM_KOS:
        if not (ov / "modules" / ko).is_file():
            raise SystemExit(f"Mono overlay missing {ko}")
    live = (ov / "single_live.py").read_text(encoding="utf-8", errors="replace")
    if "LIVE_EXPOSURE = 3600" not in live or "VIEW_W, VIEW_H" not in live:
        raise SystemExit("single_live.py is not the Ego AM color path")
    print(
        f"MONO_KIT_OK boot={hashlib.sha256(raw).hexdigest()[:16]} "
        f"module={MODULE}",
        flush=True,
    )


def pack_kit() -> Path:
    if REL.exists():
        shutil.rmtree(REL)
    REL.mkdir(parents=True)
    write_docs(REL)
    boot_src = first_file(
        EGO / "camevision_boot_ego_am.img",
        ROOT.parent / "CameVision Ego" / "restore" / "mira220-bringup" / "camevision_boot_mira220.img",
    )
    if boot_src is None:
        raise SystemExit("missing AM boot FIT — need Ego AM camevision_boot_ego_am.img")
    raw = boot_src.read_bytes()
    if not boot_ok_am(raw):
        raise SystemExit(f"{boot_src} is not a MIRA220 AM FIT")
    _copy(boot_src, REL / BOOT_NAME)
    for name in SHARED_IMGS:
        src = first_file(EGO / name, ROOT / "restore" / "known-good-20260819-camera-adb" / name)
        if src is None:
            raise SystemExit(f"missing shared image {name}")
        _copy(src, REL / name)
    ud = first_file(EGO / "userdata.img")
    if ud is not None:
        _copy(ud, REL / "userdata.img")
    stg = ROOT / "build" / "flash-userdata-mono"
    stage_overlay(stg)
    _copy_tree(stg, REL / "overlay")
    _copy(TOOLS / "S10mira220", REL / "S10mira220")
    dts = ROOT / "device-tree" / "README-AM.md"
    if dts.is_file():
        _copy(dts, REL / "device-tree" / dts.name)
    sha256sums(REL)
    verify_kit(REL)
    (ROOT / "restore" / "CURRENT-MONO.txt").write_text(
        f"{AM_RELEASE}\n"
        "This is the current CameVision Mono / MIRA220 restore point.\n"
        "One MIRA220 1600x1400 RAW10 on /dev/video1, view 1400x1600.\n"
        "Product path: python tools/cv_single_flash.py --package camevision-mono\n"
        "Live page :8081, IMU :8083. USB stays ADB.\n"
        "Do not flash gen1 serial 0558fa189447bc45.\n",
        encoding="ascii",
    )
    return REL


def main() -> int:
    rel = pack_kit()
    print(f"PACK_MONO_OK {rel}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
