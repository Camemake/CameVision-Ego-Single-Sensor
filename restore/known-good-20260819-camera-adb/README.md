# Repair point — 2026-08-19 camera + ADB

This is the first working CameVision Single snapshot: Linux boots, ADB enumerates, SC233HGS streams a real 1920x1200 frame.

Proof image: `proof-sc233hgs-1920x1200.png` (green/dark is expected — 3A is not running).

Cursor online backup is not available on this Windows PC. This folder on disk is the restore point. Do not overwrite these files.

## What is working

- Board: CameVision Single, RV1126B, 1 GB DDR4 (K4A8G165WG)
- USB gadget: Android ADB Interface `2207:0006`, strings CameMake / CameVision Single
- Sensor: SmartSens SC233HGS on i2c3 `@0x30`, 4-lane CSI, 1920x1200 SBGGR10
- ISP: `rkisp_mainpath` = `/dev/video13` NV12 1920x1200
- Capture (do this, nothing else):

```
v4l2-ctl -d /dev/video13 --set-fmt-video=width=1920,height=1200,pixelformat=NV12
timeout 12 v4l2-ctl -d /dev/video13 --stream-mmap=4 --stream-count=6 --stream-to=/userdata/camevision_frame.nv12 --stream-poll
```

## eMMC map (Aura SPL)

| name     | LBA      | file                  |
|----------|----------|-----------------------|
| env      | `0x0`    | `env.img`             |
| idblock  | `0x40`   | `idblock.img`         |
| uboot    | `0x440`  | `uboot.img`           |
| boot     | `0x2440` | `camevision_boot.img` |
| oem      | `0x207C40` | `oem_noko.img`      |
| rootfs   | `0x607C40` | `rootfs_adbwait.img`|

Boot FIT is M1 kernel + in-place bootargs only (`root=p7`, `ext4`, no pstore). Do not reserialize the DTB.

After flash, ADB-push the `overlay/` files. `oem_noko.img` does not contain the SC233HGS IQ JSON.

## Do not run (these kill USB or panic)

- `rkipc`, `RkLunch-RKIPC_RV1126B.sh`
- `simple_vi_get_frame_rkaiq`, `sample_demo_vi_venc`
- `rk_mpi_uvc`, `RkLunch-UVC_TINY.sh`
- Aura `.ko` via `insmod_ko.sh`
- UVC SuperSpeed / H.264 links in S50 before UDC bind
- `upgrade_tool db` a second time if SerialNo is already `rockchip`

## Restore

1. Fingers off BOOT. Hold BOOT, tap RESET, wait for Maskrom (`2207:110F`, empty serial).
2. Run `restore.ps1` from this folder.
3. Release BOOT, then RESET (script also tries `rd`).
4. When ADB is up, run `apply-overlay.ps1`.

Loader: `rv1126b_spl_loader_k4a8g.bin`. Download-boot only once per Maskrom session.
