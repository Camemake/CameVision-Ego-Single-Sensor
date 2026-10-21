#!/usr/bin/env python3
"""Portable CameVision Single paths for the repo and the offline installer."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

GEN1_SERIAL = "0558fa189447bc45"
MODEL_NAME = "CameVision Single"
IQ_NAME = "sc233hgs_efference-sc233hgs_default.json"
VIDEO_DEV = "/dev/video13"
CAM_W, CAM_H = 1920, 1200


def _looks_like_root(p: Path) -> bool:
    return (p / "tools").is_dir() and (
        (p / "docs" / "index.html").is_file()
        or (p / "restore" / "CURRENT-SINGLE.txt").is_file()
        or (p / "restore").is_dir()
    )


def repo_root() -> Path:
    env = os.environ.get("CAMEVISION_SINGLE_ROOT")
    if env:
        cand = Path(env).expanduser().resolve()
        if not _looks_like_root(cand):
            raise SystemExit(f"CAMEVISION_SINGLE_ROOT is not a CameVision Single tree: {cand}")
        return cand
    here = Path(__file__).resolve().parent
    for cand in (here.parent, here):
        if _looks_like_root(cand):
            return cand
    return here.parent


def host_dir() -> Path:
    return repo_root() / "host"


def is_windows() -> bool:
    return os.name == "nt"


def driver_assistant_dir() -> Path | None:
    host = host_dir()
    for cand in (
        host / "DriverAssitant_v5.14" / "DriverAssitant_v5.14",
        host / "DriverAssitant" / "DriverAssitant_v5.14",
        host / "DriverAssistant_v5.14" / "DriverAssistant_v5.14",
        host / "DriverAssitant_v5.14",
    ):
        if (cand / "DriverInstall.exe").is_file():
            return cand
    return None


def udev_rules_file() -> Path:
    return host_dir() / "linux" / "99-camevision-rockusb.rules"


def bundled_python() -> Path | None:
    host = host_dir()
    env = os.environ.get("CAMEVISION_PYTHON")
    if env and Path(env).is_file():
        return Path(env)
    if is_windows():
        return first_file(host / "python" / "python.exe", host / "python" / "pythonw.exe")
    machine = os.uname().machine.lower() if hasattr(os, "uname") else ""
    linux = host / "linux"
    if machine in ("aarch64", "arm64"):
        found = first_file(
            linux / "python-aarch64" / "bin" / "python3",
            linux / "python" / "bin" / "python3",
            host / "python" / "bin" / "python3",
        )
    else:
        found = first_file(
            linux / "python" / "bin" / "python3",
            linux / "python-aarch64" / "bin" / "python3",
            host / "python" / "bin" / "python3",
        )
    return found


def first_file(*cands: Path) -> Path | None:
    for p in cands:
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def first_dir(*cands: Path) -> Path | None:
    for p in cands:
        if p.is_dir() and any(p.iterdir()):
            return p
    return None


def adb_exe() -> str:
    env = os.environ.get("CAMEVISION_ADB")
    if env and Path(env).is_file():
        return env
    if is_windows():
        found = first_file(
            host_dir() / "adb.exe",
            host_dir() / "adb" / "adb.exe",
            Path(r"C:\Users\stefa\Downloads\RKDevTool_Release_v3.37\RKDevTool_v3.37_for_window\bin\adb.exe"),
            Path(r"C:\Users\stefa\Downloads\RKDevTool_Release_v2.84\RKDevTool_Release_v2.84\bin\adb.exe"),
        )
    else:
        found = first_file(
            host_dir() / "linux" / "adb",
            host_dir() / "adb",
            host_dir() / "platform-tools" / "adb",
        )
    if found is not None:
        return str(found)
    which = shutil.which("adb")
    if which:
        return which
    return "adb"


def upgrade_tool() -> str:
    env = os.environ.get("CAMEVISION_UPGRADE_TOOL")
    if env and Path(env).is_file():
        return env
    if is_windows():
        found = first_file(
            host_dir() / "upgrade_tool.exe",
            host_dir() / "SocToolKit" / "upgrade_tool.exe",
            Path(r"C:\Users\stefa\Downloads\SocToolKit\bin\windows\upgrade_tool.exe"),
        )
    else:
        found = first_file(
            host_dir() / "linux" / "upgrade_tool",
            host_dir() / "upgrade_tool",
        )
    if found is not None:
        return str(found)
    which = shutil.which("upgrade_tool")
    if which:
        return which
    return "upgrade_tool"


PARTITION_FILES = {
    "loader": "rv1126b_spl_loader_k4a8g.bin",
    "env": "env.img",
    "idblock": "idblock.img",
    "uboot": "uboot.img",
    "oem": "oem_noko.img",
    "rootfs": "rootfs_bootstable.img",
    "userdata": "userdata.img",
}


def known_good() -> Path:
    return repo_root() / "restore" / "known-good-20260819-camera-adb"


def current_restore() -> Path:
    return repo_root() / "restore" / "known-good-20260903-single-camera"


def update_current() -> Path:
    return repo_root() / "restore" / "updates" / "current"


def partition_img(name: str) -> Path | None:
    fname = PARTITION_FILES.get(name, name)
    root = repo_root()
    return first_file(
        update_current() / fname,
        current_restore() / fname,
        known_good() / fname,
        root / "restore" / "images" / fname,
    )


def userdata_img() -> Path | None:
    root = repo_root()
    return first_file(
        update_current() / "userdata.img",
        current_restore() / "userdata.img",
        root / "restore" / "images" / "userdata.img",
        known_good() / "userdata.img",
        root / "firmware" / "aura-stock" / "Luckfox_Aura_Buildroot_eMMC_260606" / "userdata.img",
        Path(r"C:\Users\stefa\Desktop\CameVision Single\firmware\aura-stock\Luckfox_Aura_Buildroot_eMMC_260606\userdata.img"),
    )


def boot_ok(raw: bytes) -> bool:
    return b"sc233hgs" in raw and len(raw) > 1_000_000


def boot_img() -> Path | None:
    p = first_file(
        update_current() / "camevision_boot.img",
        current_restore() / "camevision_boot.img",
        known_good() / "camevision_boot.img",
    )
    if p is None:
        return None
    if boot_ok(p.read_bytes()):
        return p
    return None


def overlay_dir() -> Path:
    return first_dir(
        update_current() / "overlay",
        current_restore() / "overlay",
        repo_root() / "tools",
    ) or current_restore() / "overlay"


def docs_dir() -> Path:
    return repo_root() / "docs"
