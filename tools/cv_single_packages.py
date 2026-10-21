#!/usr/bin/env python3
"""Selectable CameVision Single flash packages."""
from __future__ import annotations

from pathlib import Path
from shutil import which

from cv_single_paths import (
    adb_exe,
    boot_img,
    partition_img,
    repo_root,
    upgrade_tool,
    userdata_img,
)
from cv_single_paths_am import am_partition, boot_img_am, release_am

PACKAGE_PARTS = (
    "loader",
    "env",
    "idblock",
    "uboot",
    "boot",
    "userdata",
    "oem",
    "rootfs",
    "overlay",
)


def _files() -> dict[str, Path | None]:
    root = repo_root()
    overlay = root / "tools" / "single_live.py"
    return {
        "loader": partition_img("loader"),
        "env": partition_img("env"),
        "idblock": partition_img("idblock"),
        "uboot": partition_img("uboot"),
        "boot": boot_img(),
        "userdata": userdata_img(),
        "oem": partition_img("oem"),
        "rootfs": partition_img("rootfs"),
        "overlay": overlay if overlay.is_file() else None,
    }


def package_ready() -> bool:
    files = _files()
    ut = upgrade_tool()
    ut_ok = Path(ut).is_file() or which(ut) is not None
    return ut_ok and all(p is not None and Path(p).is_file() for p in files.values())


PKG_SC233 = "camevision-single"
PKG_AM = "camevision-mono"
PKG_AM_ALIASES = ("camevision-single-am", "mira220", "am", "mono-am", "mono")


def _files_am() -> dict[str, Path | None]:
    overlay = repo_root() / "tools" / "single_live.py"
    return {
        "loader": am_partition("loader"),
        "env": am_partition("env"),
        "idblock": am_partition("idblock"),
        "uboot": am_partition("uboot"),
        "boot": boot_img_am(),
        "userdata": am_partition("userdata"),
        "oem": am_partition("oem"),
        "rootfs": am_partition("rootfs"),
        "overlay": overlay if overlay.is_file() else None,
    }


def packages() -> list[dict]:
    files = _files()
    missing = [name for name, path in files.items() if path is None or not Path(path).is_file()]
    ready = package_ready()
    am_files = _files_am()
    am_missing = [name for name, path in am_files.items() if path is None or not Path(path).is_file()]
    ut = upgrade_tool()
    am_ready = (not am_missing) and (Path(ut).is_file() or which(ut) is not None)
    return [
        {
            "id": PKG_SC233,
            "name": "CameVision Single · SC233HGS",
            "sensor": "SC233HGS",
            "parts": list(PACKAGE_PARTS),
            "ready": ready,
            "missing": missing,
        },
        {
            "id": PKG_AM,
            "name": "CameVision Mono · MIRA220",
            "sensor": "MIRA220",
            "parts": list(PACKAGE_PARTS),
            "ready": am_ready,
            "missing": am_missing,
        },
    ]


def page_ready() -> bool:
    adb = adb_exe()
    overlay = _files()["overlay"]
    return overlay is not None and overlay.is_file() and (Path(adb).is_file() or adb == "adb")
