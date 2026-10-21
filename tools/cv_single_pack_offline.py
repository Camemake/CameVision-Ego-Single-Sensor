#!/usr/bin/env python3
"""Build the CameVision Single offline installer folder + zip.

Copies the mono website, live-page tools, prebuilt flash images, and
Windows host binaries into build/CameVision-Single-Offline.

    python tools/cv_single_pack_offline.py
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_single_paths import (  # noqa: E402
    IQ_NAME,
    PARTITION_FILES,
    boot_img,
    boot_ok,
    current_restore,
    known_good,
    overlay_dir,
    partition_img,
    repo_root,
    userdata_img,
)

ROOT = repo_root()
OUT = ROOT / "build" / "CameVision-Single-Offline"
ZIP = ROOT / "build" / "CameVision-Single-Offline.zip"

TOOL_FILES = (
    "cv_single_studio.py",
    "cv_single_paths.py",
    "cv_single_packages.py",
    "cv_single_driver.py",
    "cv_single_host_setup.py",
    "cv_single_setup.py",
    "cv_single_diag.py",
    "cv_single_update.py",
    "cv_single_flash.py",
    "cv_single_full_flash.py",
    "cv_single_overlay_deploy.py",
    "cv_single_page.py",
    "cv_single_autostart.py",
    "cv_single_pack_offline.py",
    "single_live.py",
    "single_imu_hud.py",
    "camevision-single.sh",
    "camevision-aiq.sh",
    "camevision-wifi.sh",
    "camevision-hw.sh",
    "camevision-led.sh",
    "camevision-imu.sh",
    "camevision-diag.sh",
    "S99camevision-single",
    "S11hwclock",
    "camemake-logo.png",
    "CameVision-Single.sh",
)

SKIP_PACK = {"schematic", "schematic-ego", "tmp", "py-tmp", "pt-tmp"}

README = """CameVision Single · offline installer
=====================================

Windows:  double-click CameVision-Single.cmd
Linux:    open CameVision-Single.sh

The Camemake window installs Python, ADB, the flash tool, and USB access.

The tool opens at http://127.0.0.1:8765/tool.html

USB / Maskrom
  Install USB driver. Hold BOOT, tap RESET, keep BOOT held.

Package
  Select CameVision Single, or load a GitHub update / a zip.
  Install. Writes loader, env, idblock, U-Boot, boot,
  userdata, oem, rootfs, and the overlay.
  Release BOOT when the board starts.
  Do not flash gen1 serial 0558fa189447bc45.

ADB
  Open: live page http://127.0.0.1:8081/  (one camera pane + 1 IMU)
  Extended diagnostics: full board dump in the log.

Same path on an empty board and on a board that already has images.
"""


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  {src} -> {dst.relative_to(OUT)}")


def _ignore(_directory: str, names: list[str]) -> set[str]:
    skip = set()
    for name in names:
        low = name.lower()
        if low in SKIP_PACK or low.startswith("schematic") or name == "parse_schematic.py":
            skip.add(name)
        if name in ("__pycache__", "tmp", ".git"):
            skip.add(name)
        if name.endswith(".zip") and "DriverAssitant" in name:
            skip.add(name)
    return skip


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=_ignore)
    n = sum(1 for p in dst.rglob("*") if p.is_file())
    print(f"  {src} -> {dst.relative_to(OUT)} ({n} files)")


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    copy_tree(ROOT / "docs", OUT / "docs")
    (OUT / "tools").mkdir(parents=True)
    for name in TOOL_FILES:
        src = ROOT / "tools" / name
        if src.is_file():
            copy_file(src, OUT / "tools" / name)
    wpa = ROOT / "tools" / "wpa_camevision.conf"
    if wpa.is_file():
        copy_file(wpa, OUT / "tools" / "wpa_camevision.conf")
    iq = ROOT / "tools" / "iqfiles" / IQ_NAME
    if iq.is_file():
        copy_file(iq, OUT / "tools" / "iqfiles" / iq.name)

    dts = ROOT / "device-tree" / "rv1126b-camevision-single.dts"
    if dts.is_file():
        copy_file(dts, OUT / "device-tree" / dts.name)

    cur_out = OUT / "restore" / "known-good-20260903-single-camera"
    kg_out = OUT / "restore" / "known-good-20260819-camera-adb"
    cur_out.mkdir(parents=True)
    kg_out.mkdir(parents=True)

    boot = boot_img()
    if boot is None:
        raise SystemExit("no CameVision Single boot to pack — refuse to ship")
    raw = boot.read_bytes()
    if not boot_ok(raw):
        raise SystemExit(f"boot {boot} is not a CameVision Single FIT")
    copy_file(boot, cur_out / "camevision_boot.img")
    (cur_out / "BOOT.sha256").write_text(
        hashlib.sha256(raw).hexdigest() + "  camevision_boot.img\n",
        encoding="ascii",
    )

    for key, fname in PARTITION_FILES.items():
        if key == "userdata":
            src = userdata_img()
        else:
            src = partition_img(key)
        if src is None or not src.is_file():
            raise SystemExit(f"missing CameVision image {fname}")
        dest_dir = kg_out if key != "boot" else cur_out
        if key == "userdata":
            dest_dir = kg_out
        copy_file(src, dest_dir / fname)

    src_ov = overlay_dir()
    for folder in ("swt6621-rt52", "swt6621_fw", "iqfiles"):
        src = src_ov / folder
        if src.is_dir():
            copy_tree(src, cur_out / "overlay" / folder)
    for name in (
        "camevision-aiq.sh",
        "camevision-wifi.sh",
        "camevision-hw.sh",
        "camevision-led.sh",
        "camevision-imu.sh",
        "camevision-diag.sh",
        "wpa_camevision.conf",
        "S50usbdevice",
        "S99camevision",
    ):
        src = src_ov / name
        if src.is_file():
            copy_file(src, cur_out / "overlay" / name)
    for ko_src in (
        src_ov / "kmpp-rt52.ko",
        ROOT / "restore" / "recovery-3-20260822-uvc-wifi-rkaiq" / "overlay" / "kmpp-rt52.ko",
        ROOT / "restore" / "recovery-2-20260821-adb-stream" / "overlay" / "kmpp-rt52.ko",
    ):
        if ko_src.is_file():
            copy_file(ko_src, cur_out / "overlay" / "kmpp-rt52.ko")
            break
    else:
        print("WARN kmpp-rt52.ko not found")

    (OUT / "restore" / "CURRENT-SINGLE.txt").write_text(
        "known-good-20260903-single-camera\n"
        "CameVision Single offline pack. USB stays ADB. One camera, one IMU.\n"
        "Do not flash gen1 serial 0558fa189447bc45.\n",
        encoding="ascii",
    )

    host = OUT / "host"
    host.mkdir(parents=True)
    src_host = ROOT / "host"
    win_adb = src_host / "adb.exe"
    if win_adb.is_file():
        copy_file(win_adb, host / "adb.exe")
        for extra in ("AdbWinApi.dll", "AdbWinUsbApi.dll"):
            sib = src_host / extra
            if sib.is_file():
                copy_file(sib, host / extra)
    else:
        print("WARN host/adb.exe not found")
    win_ut = src_host / "upgrade_tool.exe"
    if win_ut.is_file():
        copy_file(win_ut, host / "upgrade_tool.exe")
    else:
        print("WARN host/upgrade_tool.exe not found")

    da = src_host / "DriverAssitant_v5.14"
    if da.is_dir():
        copy_tree(da, host / "DriverAssitant_v5.14")
    else:
        print("WARN host/DriverAssitant_v5.14 not found — USB driver will be missing")

    linux_src = src_host / "linux"
    if linux_src.is_dir():
        (host / "linux").mkdir(parents=True, exist_ok=True)
        for p in linux_src.iterdir():
            if p.name in ("py-tmp", "pt-tmp", "tmp"):
                continue
            if p.is_dir():
                copy_tree(p, host / "linux" / p.name)
            elif p.is_file():
                copy_file(p, host / "linux" / p.name)

    py_src = src_host / "python"
    if py_src.is_dir() and (py_src / "python.exe").is_file():
        copy_tree(py_src, host / "python")

    for name in ("CameVision-Single.cmd", "CameVision-Single.sh"):
        src = ROOT / name
        if src.is_file():
            copy_file(src, OUT / name)
            if name.endswith(".sh"):
                os.chmod(OUT / name, 0o755)
    (OUT / "README.txt").write_text(README, encoding="utf-8")
    (OUT / "VERSION").write_text("CameVision-Single-Offline 0.1\n", encoding="ascii")

    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in OUT.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(OUT.parent))
    print(f"wrote {OUT}")
    print(f"wrote {ZIP} ({ZIP.stat().st_size} bytes)")
    _verify_pack(OUT)
    return 0


ALLOWED_IMGS = {
    "camevision_boot.img",
    "env.img",
    "idblock.img",
    "uboot.img",
    "oem_noko.img",
    "rootfs_bootstable.img",
    "userdata.img",
}
ALLOWED_BINS = {"rv1126b_spl_loader_k4a8g.bin"}
FORBIDDEN_DIR_BITS = (
    "recovery-",
    "lock-",
    "diag-adb",
    "firmware",
    "updates",
    "rootfs_adbwait",
)


def _verify_pack(out: Path) -> None:
    env = os.environ.get("CAMEVISION_SINGLE_ROOT")
    os.environ["CAMEVISION_SINGLE_ROOT"] = str(out)
    try:
        from cv_single_packages import packages
        from cv_single_paths import boot_img as packed_boot
        from cv_single_paths import boot_ok as packed_ok
        from cv_single_paths import partition_img as packed_part
        from cv_single_paths import userdata_img as packed_ud

        img = packed_boot()
        if img is None or not packed_ok(img.read_bytes()):
            raise SystemExit("packed tree has no CameVision Single boot")
        live = out / "tools" / "single_live.py"
        sh = out / "tools" / "camevision-single.sh"
        ov = out / "tools" / "cv_single_overlay_deploy.py"
        if not live.is_file() or not sh.is_file() or not ov.is_file():
            raise SystemExit("packed tree missing mono live overlay scripts")
        text = live.read_text(encoding="utf-8")
        if "scale(-1,-1)" in text or "ego_stereo" in text:
            raise SystemExit("packed live page still has Ego stereo / CSS 180")
        if "/dev/video13" not in text:
            raise SystemExit("packed live page is not the mono /dev/video13 layout")
        docs = out / "docs"
        for name in (
            "index.html",
            "start.html",
            "tool.html",
            "hardware.html",
            "mechanical.html",
            "optics.html",
            "software.html",
            "datasheet.html",
        ):
            if not (docs / name).is_file():
                raise SystemExit(f"packed docs missing {name}")
        boots = [p for p in out.rglob("camevision_boot*.img") if p.is_file()]
        if len(boots) != 1:
            raise SystemExit(
                "pack must contain exactly one camevision_boot*.img, got "
                + ", ".join(str(p.relative_to(out)) for p in boots)
            )
        raw = boots[0].read_bytes()
        if not packed_ok(raw):
            raise SystemExit(f"packed boot is not CameVision Single: {boots[0]}")
        restore = out / "restore"
        extra_dirs = [
            p.name
            for p in restore.iterdir()
            if p.is_dir()
            and p.name
            not in ("known-good-20260903-single-camera", "known-good-20260819-camera-adb")
        ]
        if extra_dirs:
            raise SystemExit("pack has leftover restore trees: " + ", ".join(extra_dirs))
        for p in restore.rglob("*"):
            rel = str(p.relative_to(out)).replace("\\", "/").lower()
            if any(bit in rel for bit in FORBIDDEN_DIR_BITS):
                raise SystemExit(f"pack still contains old tree {p.relative_to(out)}")
        imgs = [p for p in out.rglob("*.img") if p.is_file()]
        extra_imgs = [p for p in imgs if p.name not in ALLOWED_IMGS]
        if extra_imgs:
            raise SystemExit(
                "pack has unused images: "
                + ", ".join(str(p.relative_to(out)) for p in extra_imgs)
            )
        missing_imgs = [name for name in ALLOWED_IMGS if not any(p.name == name for p in imgs)]
        if missing_imgs:
            raise SystemExit("pack missing images: " + ", ".join(missing_imgs))
        for key in PARTITION_FILES:
            if key == "userdata":
                continue
            if packed_part(key) is None:
                raise SystemExit(f"packed tree cannot resolve {key}")
        if packed_ud() is None:
            raise SystemExit("packed tree cannot resolve userdata")
        pkgs = packages()
        if len(pkgs) != 1 or pkgs[0]["id"] != "camevision-single":
            raise SystemExit("pack must expose only CameVision Single")
        if not pkgs[0]["ready"]:
            raise SystemExit("CameVision Single package is not ready: " + ", ".join(pkgs[0]["missing"]))
        if not (out / "CameVision-Single.cmd").is_file():
            raise SystemExit("pack missing CameVision-Single.cmd")
        print(
            f"PACK_OK boot={img} sha={hashlib.sha256(raw).hexdigest()[:16]} "
            f"imgs={len(imgs)}",
            flush=True,
        )
    finally:
        if env is None:
            os.environ.pop("CAMEVISION_SINGLE_ROOT", None)
        else:
            os.environ["CAMEVISION_SINGLE_ROOT"] = env


if __name__ == "__main__":
    raise SystemExit(main())
