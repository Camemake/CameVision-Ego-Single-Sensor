#!/usr/bin/env python3
"""Maskrom flash for CameVision Mono / MIRA220 only.

Never reads the SC233HGS Single boot. USB stays ADB.

    python tools/cv_single_flash_am.py
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import GEN1_SERIAL, adb_exe, upgrade_tool  # noqa: E402
from cv_single_paths_am import (  # noqa: E402
    MODULE,
    am_partition,
    boot_img_am,
    boot_ok_am,
    release_am,
)

UT = upgrade_tool()
ADB = adb_exe()
REL = release_am()
LOADER = am_partition("loader")


def boot_img() -> Path:
    p = boot_img_am()
    if p is None:
        raise SystemExit(f"missing AM boot FIT in {REL}")
    raw = p.read_bytes()
    if not boot_ok_am(raw):
        raise SystemExit(f"{p} is not a MIRA220 AM boot")
    print(f"boot {p} sha256={hashlib.sha256(raw).hexdigest()}", flush=True)
    return p


def staged_boot() -> Path:
    src = boot_img()
    dst = Path(os.environ.get("TEMP") or "/tmp") / "camevision_boot_single_am.img"
    shutil.copy2(src, dst)
    if not boot_ok_am(dst.read_bytes()):
        raise SystemExit("staged AM boot failed check")
    return dst


def writes() -> tuple[tuple[str, Path], ...]:
    parts = {
        "env": am_partition("env"),
        "idblock": am_partition("idblock"),
        "uboot": am_partition("uboot"),
        "userdata": am_partition("userdata"),
        "oem": am_partition("oem"),
        "rootfs": am_partition("rootfs"),
    }
    missing = [n for n, p in parts.items() if p is None]
    if missing:
        raise SystemExit("missing AM images: " + ", ".join(missing))
    return (
        ("0x0", parts["env"]),
        ("0x40", parts["idblock"]),
        ("0x440", parts["uboot"]),
        ("0x2440", staged_boot()),
        ("0x7C40", parts["userdata"]),
        ("0x207C40", parts["oem"]),
        ("0x607C40", parts["rootfs"]),
    )


def run(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    print(">", " ".join(args), flush=True)
    r = subprocess.run(args, capture_output=True, timeout=timeout)
    text = ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")
    if text.strip():
        print(text, end="" if text.endswith("\n") else "\n", flush=True)
    return r


def ld() -> str:
    r = run([UT, "ld"], timeout=30)
    return ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")


def pick_serial(listing: str) -> str | None:
    found = []
    for line in listing.splitlines():
        if "\tdevice" not in line:
            continue
        serial = line.split()[0]
        if serial == GEN1_SERIAL:
            print("skipping gen1 ADB", serial, flush=True)
            continue
        found.append(serial)
    return found[0] if found else None


def main() -> int:
    if LOADER is None or not LOADER.is_file():
        raise SystemExit(f"missing AM loader in {REL}")
    parts = writes()
    for _, p in parts:
        print(f"  {p.name:32s} {p.stat().st_size:12d}", flush=True)

    info = ld()
    if "Maskrom" not in info and "Loader" not in info:
        raise SystemExit("no Rockusb device — hold BOOT, tap RESET")

    loaded = ("SerialNo=rockchip" in info) or ("SerialNo=0" in info)
    if "Maskrom" in info and not loaded:
        print("=== db loader once ===", flush=True)
        r = run([UT, "db", str(LOADER)], timeout=60)
        if r.returncode != 0:
            raise SystemExit("db failed")
        time.sleep(2)
        info = ld()
        if "SerialNo=rockchip" not in info and "SerialNo=0" not in info:
            raise SystemExit("loader did not stay up")
    else:
        print("=== skip db ===", flush=True)

    for lba, path in parts:
        print(f"=== wl {lba} {path.name} ({path.stat().st_size} bytes) ===", flush=True)
        r = run([UT, "wl", lba, str(path)], timeout=900)
        if r.returncode != 0:
            raise SystemExit(f"write failed {path.name}")

    print("=== RELEASE BOOT NOW — waiting 8s ===", flush=True)
    time.sleep(8)
    print("=== rd ===", flush=True)
    run([UT, "rd"], timeout=30)

    t0 = time.time()
    serial = None
    while time.time() - t0 < 150:
        time.sleep(4)
        listing = subprocess.run([ADB, "devices"], capture_output=True, text=True).stdout
        print(f"t={time.time()-t0:.0f}s adb={listing.strip()!r}", flush=True)
        serial = pick_serial(listing)
        if serial:
            break
    if not serial:
        raise SystemExit("board did not enumerate ADB — release BOOT if it is held")

    import cv_single_overlay_deploy_am

    cv_single_overlay_deploy_am.deploy(serial)
    names = cv_single_overlay_deploy_am._module_names(serial)
    if MODULE not in names:
        raise SystemExit("flashed board is not camevision-mira220")
    print("SINGLE_AM_UP", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
