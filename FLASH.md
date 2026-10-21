# Flash from Maskrom

Empty board or a board that already has images. USB stays ADB
(`2207:0006` after boot). Do not switch to a UVC webcam.

## Kits

| Package | Restore | Boot image | Sensor |
|---|---|---|---|
| `camevision-single` | `restore/known-good-20260903-single-camera` | `camevision_boot.img` | SC233HGS `/dev/video13` |
| `camevision-mono` | `restore/release-1.0-mono-mira220-20261014` | `camevision_boot_mono.img` | MIRA220 `/dev/video1` |

Shared SPL / oem / rootfs: `restore/known-good-20260819-camera-adb`.

## What you need

- The matching board (Single SC233 or Mono AM / MIRA220)
- USB-C cable that carries data
- Python 3.10+ (or `host/python` in an offline pack)
- Rockchip USB: `host/DriverAssitant_v5.14` (Windows) or `host/linux/` udev
- `git lfs pull` so `oem_noko.img`, `rootfs_bootstable.img`, `userdata.img` are real files

## Enter Maskrom

1. Power the board (USB-C is enough).
2. Hold **BOOT**.
3. Tap **RESET**.
4. Keep BOOT held until `upgrade_tool ld` shows Maskrom (`2207:110f`) or Loader.

```
python tools/cv_single_flash.py --package camevision-single
python tools/cv_single_flash.py --package camevision-mono
```

Or the installer: `python tools/cv_single_studio.py` → http://127.0.0.1:8765/tool.html

Release BOOT when the write finishes and the board starts.

`upgrade_tool db` (loader) only **once** per Maskrom session. After `db` the
port re-enumerates as Loader (`SerialNo=rockchip`). After `rd` + BOOT released,
the gadget is ADB.

Do not flash gen1 serial `0558fa189447bc45`.

## Partition map

| LBA | Image | Role |
|---|---|---|
| loader (`db` once) | `rv1126b_spl_loader_k4a8g.bin` | SPL, 1 GB DDR |
| `0x0` | `env.img` | U-Boot env |
| `0x40` | `idblock.img` | idblock |
| `0x440` | `uboot.img` | U-Boot |
| `0x2440` | `camevision_boot.img` or `camevision_boot_mono.img` | Kernel + DTB FIT (`6.1.141-rt52`) |
| `0x7C40` | `userdata.img` | Skeleton, then ADB overlay |
| `0x207C40` | `oem_noko.img` | oem libs, rkaiq bits |
| `0x607C40` | `rootfs_bootstable.img` | Root filesystem |

Overlay is not a partition. After ADB is up:

```
python tools/cv_single_overlay_deploy.py        # SC233
python tools/cv_single_overlay_deploy_am.py     # Mono / MIRA220
```

Manual `upgrade_tool` (Windows; Linux is `host/linux/upgrade_tool`):

```
upgrade_tool ld
upgrade_tool db restore/known-good-20260819-camera-adb/rv1126b_spl_loader_k4a8g.bin
upgrade_tool wl 0x0     restore/known-good-20260819-camera-adb/env.img
upgrade_tool wl 0x40    restore/known-good-20260819-camera-adb/idblock.img
upgrade_tool wl 0x440   restore/known-good-20260819-camera-adb/uboot.img
upgrade_tool wl 0x2440  restore/known-good-20260903-single-camera/camevision_boot.img
upgrade_tool wl 0x7C40  restore/known-good-20260819-camera-adb/userdata.img
upgrade_tool wl 0x207C40 restore/known-good-20260819-camera-adb/oem_noko.img
upgrade_tool wl 0x607C40 restore/known-good-20260819-camera-adb/rootfs_bootstable.img
upgrade_tool rd
```

For Mono, write `restore/release-1.0-mono-mira220-20261014/camevision_boot_mono.img`
at `0x2440` instead.

## After first boot

| Check | Expect |
|---|---|
| ADB | `adb devices` shows a serial that is not `0558fa189447bc45` |
| SC233 live | `/stat` → 1920×1200 NV12, `/dev/video13` |
| Mono live | `/stat` → 1400×1600 BG10, `/dev/video1`, ~30 fps |
| Mono regs | VSTART `0x107D`=0, exp `0x100C`=3600, vblank `0x1012`=2695 |
| IMU | `:8083` → `imu0` on SPI1 (Single) or `spi0.0` (Mono), \|a\| ≈ 1 g |

Live: http://127.0.0.1:8081/ after `adb forward tcp:8081 tcp:8081`.
