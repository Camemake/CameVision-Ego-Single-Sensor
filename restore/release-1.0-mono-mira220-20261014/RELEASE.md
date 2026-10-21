# CameVision Mono · MIRA220 · 1.0 — 14 October 2026

This folder is the **Mono / MIRA220** kit. It is **not** the SC233HGS
Single kit (`restore/known-good-20260903-single-camera`) and **not** Ego
stereo. Do not flash one onto the other.

Hardware: CameVisionMono_OV V0.3, one AMS MIRA220 (1600×1400 RAW10, GRBG),
one LSM6 on SPI0. Live view is 1400×1600 after 90° CCW. USB stays **ADB**.

```
python tools/cv_single_flash.py --package camevision-mono
python tools/cv_single_overlay_deploy_am.py
```

| Partition | Image |
|---|---|
| env / idblock / uboot | same RV1126B SPL set as Ego AM |
| boot | `camevision_boot_mono.img` (MIRA220 DTB; CAM1 unused) |
| userdata | Mono overlay (CIF CAM0, mira modules, MIRA220 IQ) |
| oem / rootfs | CameVision `oem_noko.img` / `rootfs_bootstable.img` |

Overlay:

- Live page `:8081` — CIF RAW10, Ego AM color path, 1400×1600
- IMU HUD `:8083` — IMU0 only
- `S10mira220` — CAM0 power + mira220 + ciflate + miralink
- IQ `mira220_camevision-mira220_default.json`
- Color decoder `libsingle_color.so` (`ego_raw10_color_nv12`)
- Exposure 3600, vblank 2695, VSTART 0 (re-applied after stream-on)

## Do not

- Flash this kit onto a SC233HGS board
- Use `tools/cv_single_flash.py` without `--package camevision-mono`
- Ship `ego_stereo.py` or start a second camera
- Switch USB to a webcam gadget
