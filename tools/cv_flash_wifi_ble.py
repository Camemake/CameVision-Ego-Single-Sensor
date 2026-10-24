#!/usr/bin/env python3
"""Maskrom flash CameVision Mono, then Wi-Fi + BLE. No USB gadget wait."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_flash_am import LOADER, UT, ld, run, writes  # noqa: E402


def main() -> int:
    if LOADER is None or not LOADER.is_file():
        raise SystemExit("missing AM loader")
    parts = writes()
    for lba, p in parts:
        print(f"  {lba:10s} {p.name:32s} {p.stat().st_size:12d}", flush=True)

    info = ld()
    if "Maskrom" not in info and "Loader" not in info:
        raise SystemExit("no Rockusb — hold BOOT, tap RESET")

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
    print("FLASH_OK wait for wlan0/telnet — no ADB gadget required", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
