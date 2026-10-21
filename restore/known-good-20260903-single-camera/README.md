# Repair point — 2026-09-03 CameVision Single camera

This is the **current** CameVision Single snapshot: Gen2 board, ADB, Wi-Fi, IMU, and a live SC233HGS that probes and streams.

Do not overwrite these files. Do not flash the Gen1 board `0558fa189447bc45`.

Proof still: `proof-sc233hgs-1920x1200.png` (green/soft is expected — 3A is not required for this lock). Raw NV12: `proof-sc233hgs-1920x1200.nv12`.

## What is working

- Board: CameVision Single Gen2, RV1126B, serial `02a9cda75adc57e7`
- USB gadget: ADB only `2207:0006`, product CameVision Single
- Kernel: `6.1.141-rt52` `#24 SMP PREEMPT_RT`
- DT model: `CameVision Single`
- Sensor: SmartSens SC233HGS on i2c3 `@0x30`, chip id `0xcb61`, 4-lane CSI RX0
- ISP: `rkisp_mainpath` = `/dev/video13` NV12 1920×1200
- Wi-Fi: Seekwave VS6621 on mmc2, `WIFI_RST` GPIO3_B2
- Camera LDOs: kernel gpio-regulators GPIO0_B0 / GPIO0_B1 (AVDD 2.8 V, DVDD 1.5 V)
- `CAM_PWDN` GPIO4_A6 is `reset-gpios` **ACTIVE_LOW** (run = high). This is the M1 polarity. Do not flip it to ACTIVE_HIGH.
- xvclk is CRU clock `0x6d` = `clk_mipi0_out2io` on `CAM_CLK0_OUT` (GPIO4_B1)

Capture (do this, nothing else):

```
v4l2-ctl -d /dev/video13 --set-fmt-video=width=1920,height=1200,pixelformat=NV12
timeout 12 v4l2-ctl -d /dev/video13 --stream-mmap=4 --stream-count=6 --stream-to=/userdata/camevision_frame.nv12 --stream-poll
```

## Why this boot exists

The 2026-08-19 M1 copy already had a working camera. The Gen2 Single v5 boot patch set `reset-gpios` to ACTIVE_HIGH, which held PWDN low, so chip-id failed with `-5` and xvclk was released. This image is the diag-ADB FIT with only that cell restored to ACTIVE_LOW. LDO gpio-regulators stay.

## eMMC map (Aura SPL)

| name     | LBA        | file |
|----------|------------|------|
| env      | `0x0`      | `known-good-20260819-camera-adb/env.img` |
| idblock  | `0x40`     | `known-good-20260819-camera-adb/idblock.img` |
| uboot    | `0x440`    | `known-good-20260819-camera-adb/uboot.img` |
| boot     | `0x2440`   | **this folder** `camevision_boot.img` |
| userdata | `0x7C40`   | aura-stock `userdata.img` (overlay after boot) |
| oem      | `0x207C40` | `known-good-20260819-camera-adb/oem_noko.img` |
| rootfs   | `0x607C40` | `known-good-20260819-camera-adb/rootfs_bootstable.img` |

## Do not run

- `rkipc`, `RkLunch-RKIPC_RV1126B.sh`
- `simple_vi_get_frame_rkaiq`, `sample_demo_vi_venc`
- `rk_mpi_uvc`, `RkLunch-UVC_TINY.sh`
- Aura `.ko` via `insmod_ko.sh`
- Ego stereo / webpage (`ego_stereo.py`, ports 8081/8083)
- `upgrade_tool db` a second time if SerialNo is already `rockchip`

## Restore

1. Fingers off BOOT. Hold BOOT, tap RESET, wait for Maskrom (`2207:110F`).
2. Run `restore.ps1` from this folder.
3. Release BOOT after it prints `rd`.
4. Overlay is applied automatically when ADB is up. If not: `apply-overlay.ps1`.

Loader: `known-good-20260819-camera-adb/rv1126b_spl_loader_k4a8g.bin`. Download-boot only once per Maskrom session.
