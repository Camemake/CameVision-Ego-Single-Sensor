#!/usr/bin/env python3
"""Paths for the CameVision Mono / MIRA220 kit.

Never resolve the SC233HGS Single boot. Ego is only a sibling fallback
when this tree does not yet have its own restore kit.
"""
from __future__ import annotations

from pathlib import Path

from cv_single_paths import first_file, repo_root

AM_RELEASE = "release-1.1-mono-mira220-20261023"
EGO_AM_RELEASE = "release-2.0-am-mira220-20261009"
BOOT_NAME = "camevision_boot_mono.img"
BOOT_WIFI_NAME = "camevision_boot_mono_wifi.img"
BOOT_NAMES = (
    BOOT_WIFI_NAME,
    BOOT_NAME,
    "camevision_boot_single_am.img",
    "camevision_boot_ego_am.img",
)
MODULE = "camevision-mira220"
IQ_NAME_AM = "mira220_camevision-mira220_default.json"
VIDEO_DEV_AM = "/dev/video1"
CAM_W_AM, CAM_H_AM = 1600, 1400


def release_am() -> Path:
    root = repo_root()
    local = root / "restore" / AM_RELEASE
    if any((local / name).is_file() for name in BOOT_NAMES):
        return local
    ego = root.parent / "CameVision Ego" / "restore" / EGO_AM_RELEASE
    if ego.is_dir():
        return ego
    return local


def boot_ok_am(raw: bytes) -> bool:
    if raw.count(MODULE.encode("ascii")) < 1:
        return False
    if b"camevision-sc233hgs" in raw and raw.count(MODULE.encode("ascii")) < 1:
        return False
    if b"efference-sc233hgs" in raw:
        return False
    return True


def boot_img_am() -> Path | None:
    rel = release_am()
    for name in BOOT_NAMES:
        p = first_file(rel / name)
        if p is not None and boot_ok_am(p.read_bytes()):
            return p
    return None


def am_partition(name: str) -> Path | None:
    names = {
        "loader": "rv1126b_spl_loader_k4a8g.bin",
        "env": "env.img",
        "idblock": "idblock.img",
        "uboot": "uboot.img",
        "oem": "oem_noko.img",
        "rootfs": "rootfs_bootstable.img",
        "userdata": "userdata.img",
        "boot": BOOT_NAMES[0],
    }
    fname = names.get(name, name)
    rel = release_am()
    found = first_file(rel / fname)
    if found is not None:
        return found
    if name == "boot":
        return boot_img_am()
    from cv_single_paths import partition_img, userdata_img

    if name == "userdata":
        return userdata_img()
    return partition_img(name)


def am_overlay_dir() -> Path:
    rel = release_am()
    ov = rel / "overlay"
    if ov.is_dir():
        return ov
    return repo_root() / "tools"


def am_module(name: str) -> Path | None:
    rel = release_am()
    tools = repo_root() / "tools"
    return first_file(
        tools / "am-modules" / name,
        am_overlay_dir() / "modules" / name,
        am_overlay_dir() / name,
        rel / "driver" / name,
        rel / name,
    )
