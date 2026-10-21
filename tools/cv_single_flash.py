#!/usr/bin/env python3
"""CameVision Single Maskrom package install.

Writes loader, env, idblock, U-Boot, boot, userdata, oem, rootfs, then
the overlay. Same sequence on an empty board and on a flashed board.

    python tools/cv_single_flash.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import boot_img, repo_root  # noqa: E402

ROOT = repo_root()
sys.path.insert(0, str(ROOT / "tools"))
import cv_single_full_flash  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="CameVision Single Maskrom package install")
    p.add_argument(
        "--prebuilt",
        action="store_true",
        help="write existing boot/overlay images (offline installer default)",
    )
    p.add_argument(
        "--package",
        default="camevision-single",
        help="package id from the offline tool",
    )
    args = p.parse_args()
    pkg = (args.package or "camevision-single").strip().lower()
    if pkg in (
        "camevision-mono",
        "camevision-single-am",
        "mira220",
        "am",
        "mono-am",
        "mono",
    ):
        import cv_single_flash_am

        print("=== install camevision-mono  MIRA220 ===", flush=True)
        print("=== Maskrom write + Mono / MIRA220 overlay ===", flush=True)
        return cv_single_flash_am.main()
    if boot_img() is None:
        raise SystemExit(
            "missing camevision_boot.img — expected in restore/known-good-20260903-single-camera"
        )
    print(f"=== install {args.package} ===", flush=True)
    print("=== using prebuilt CameVision Single boot FIT ===", flush=True)
    print("=== Maskrom write + overlay ===", flush=True)
    return cv_single_full_flash.main()


if __name__ == "__main__":
    raise SystemExit(main())
