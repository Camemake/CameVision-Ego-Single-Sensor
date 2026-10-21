# CameVision Single / Mono

Developer tree for the one-camera CameVision boards. Two Maskrom kits in
one repo. USB stays **ADB**. Do not switch the gadget to UVC.

| Package | Board | Sensor | Live |
|---|---|---|---|
| `camevision-single` | CameVision Single | SmartSens SC233HGS 1920×1200 NV12 | `/dev/video13` |
| `camevision-mono` | CameVision Mono (AM) | AMS MIRA220 1600×1400 RAW10 | `/dev/video1` → 1400×1600 |

Both kits: RV1126B, 1× IMU, Wi-Fi 6 (VS6621), eMMC. Overlay and live page
run on the board. The host only flashes and opens a browser.

Do not flash gen1 serial `0558fa189447bc45`.

## Empty Maskrom board

Same path on a blank eMMC and on a board that already has images.

1. USB-C data cable. Hold **BOOT**, tap **RESET**, keep BOOT held.
2. Windows: double-click `CameVision-Single.exe` (bundled Python, no system
   install). Linux: `CameVision-Single` or `CameVision-Single.sh`.
   Fallback: `CameVision-Single.cmd` or `python tools/cv_single_studio.py`
3. Installer at http://127.0.0.1:8765/tool.html
4. **USB** — install the Rockchip driver (`host/DriverAssitant_v5.14`).
5. **Package** — pick **CameVision Single · SC233HGS** or **CameVision Mono · MIRA220**.
6. **Install** — writes loader, env, idblock, U-Boot, boot, userdata, oem,
   rootfs, then the overlay. Release BOOT when the board starts.
7. **Open** — live page http://127.0.0.1:8081/  IMU http://127.0.0.1:8083/

Command line:

```
python tools/cv_single_flash.py --package camevision-single
python tools/cv_single_flash.py --package camevision-mono
python tools/cv_single_overlay_deploy.py
python tools/cv_single_overlay_deploy_am.py
python tools/cv_single_page.py
```

Need: `git lfs pull` after clone (oem / rootfs / userdata). Windows
needs no system Python — `host/python` ships in the tree. Linux extracts
`host/linux/python-*.tar.gz` on first run.
Rockchip USB: Windows driver in `host/DriverAssitant_v5.14`, Linux udev in
`host/linux/`. `upgrade_tool db` only **once** per Maskrom session.

Full LBA map and image names: [`FLASH.md`](FLASH.md).
Board nets, GPIOs, I2C/SPI: [`HARDWARE.md`](HARDWARE.md).

## Layout

```
CameVision-Single.exe           Windows installer (bundled Python)
CameVision-Single / .sh         Linux installer
CameVision-Single.cmd           Windows cmd fallback
tools/                          Flash, overlay, live, IMU, IQ, modules
  installer/                    C# source for CameVision-Single.exe
  cv_single_studio.py           Installer HTTP :8765
  cv_single_flash.py            Maskrom write, then overlay
  cv_single_overlay_deploy.py   SC233 ADB overlay
  cv_single_overlay_deploy_am.py
  single_live.py                Live page :8081
  single_imu_hud.py             IMU HUD :8083
  S10mira220                    Mono CAM0 bring-up
  libsingle_color.so            MIRA220 RAW10 → NV12 (Ego AM color path)
device-tree/                    SC233 DTS + Mono AM notes
restore/known-good-20260819-camera-adb/   SPL, env, uboot, oem, rootfs
restore/known-good-20260903-single-camera/  SC233 boot FIT + overlay
restore/release-1.0-mono-mira220-20261014/  Mono boot FIT + overlay
docs/tool.html                  Installer UI
host/                           adb, upgrade_tool, Rockchip USB driver
host/python                     Windows Python 3.12 embed
host/linux/python-*.tar.gz      Linux Python (x86_64 / aarch64)
```

## Rebuild / pack

```
python tools/cv_single_pack_mono.py      # refresh the Mono restore kit
python tools/cv_single_pack_offline.py   # Windows/Linux offline folder + zip
```

## Do not

- Flash this onto CameVision Ego (stereo) or the other way around
- Mix SC233 and MIRA220 images on the same board
- Commit `wpa_camevision.conf` (local Wi-Fi)
- Ship `ego_stereo.py` or start a second camera on Mono
