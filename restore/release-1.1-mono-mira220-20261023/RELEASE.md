# CameVision Mono · MIRA220 · 1.1 — 23 October 2026

This is the current **Mono / MIRA220** release. It replaces the 1.0 kit
and the later Wi-Fi/BLE and UVC restore points. It is **not** the
SC233HGS Single kit (`restore/known-good-20260903-single-camera`) and
**not** Ego stereo. Do not flash one onto the other.

Hardware: CameVisionMono_OV V0.3, one AMS MIRA220 (1600×1400 RAW10, GRBG),
one LSM6 on SPI0. Live view is 1400×1600 after 90° CCW.

USB starts as official **ADB** (`2207:0006`). After Wi-Fi is up, boot
binds the **Camemake** UVC gadget (`2207:0016`, MJPEG 1400×1600). Official
S50 stays on disk so a reboot without Wi-Fi comes back as ADB. Telnet
`:2323` is the shell while UVC holds USB.

```
python tools/cv_single_flash.py --package camevision-mono
python tools/cv_single_overlay_deploy_am.py
```

| Partition | Image |
|---|---|
| env / idblock / uboot | same RV1126B SPL set as Ego AM |
| boot | `camevision_boot_mono_wifi.img` (WIFI_RST GPIO0_A0, wake B6/B7) |
| userdata | Mono overlay (CIF CAM0, mira, Wi-Fi/BLE, Camemake UVC) |
| oem / rootfs | CameVision `oem_noko.img` / `rootfs_bootstable.img` |

Overlay:

- Live page `:8081` — CIF RAW10, Ego AM color path, 1400×1600
- IMU HUD `:8083` — IMU0 only
- `S10mira220` — CAM0 power + mira220 + ciflate + miralink
- IQ `mira220_camevision-mira220_default.json`
- Color decoder `libsingle_color.so` (`ego_raw10_color_nv12`)
- Exposure 3600, vblank 2695, VSTART 0 (re-applied after stream-on)
- Wi-Fi + BLE on the VS6621 shared antenna (SHARE NV + 48-byte NVDS)
- Bluetooth name `CameVision Ego Single` + last 6 MAC hex digits
- Camemake UVC via `_lock_uvc_safe.sh` + `camevision-uvc-bridge.py`
- Composite USB: UVC `2207:0016` + mass-storage of the microSD
- MJPEG 1400×1600 / 1050×1200 / 700×800 / 350×400 at 60 / 30 / 15
- Phone app CameVision 0.1 (Bluetooth preview / record / card) — https://github.com/Camemake/CameVision-App

## Do not

- Flash this kit onto a SC233HGS board
- Use `tools/cv_single_flash.py` without `--package camevision-mono`
- Ship `ego_stereo.py` or start a second camera
- Persist `uvc-webcam.on` or leave a stub S50 on disk
- Copy SHARE (220 B) over `sv6160lite.nvbin`
- Flash gen1 serial `0558fa189447bc45`
