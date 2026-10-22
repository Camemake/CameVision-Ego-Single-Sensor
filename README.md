<p align="center">
  <img src="tools/camemake-logo.png" alt="Camemake" width="280">
</p>

<h1 align="center">CameVision Ego Single Sensor</h1>

<p align="center">
  <strong>CV-EGO01-SS</strong> · One global-shutter camera, one IMU
</p>

<p align="center">
  <a href="https://www.camemake.eu/shop/camevision-ego-single-sensor-4547"><strong>Shop</strong></a>
  ·
  <a href="https://camemake.github.io/CameVision-Ego-Single-Sensor/"><strong>Product page</strong></a>
  ·
  <a href="https://camemake.github.io/CameVision-Ego-Single-Sensor/zh/"><strong>中文</strong></a>
  ·
  <a href="https://www.camemake.eu/robotic-solutions"><strong>Camemake robotic solutions</strong></a>
  ·
  <a href="https://github.com/Camemake/CameVision-Ego"><strong>CameVision Ego (stereo)</strong></a>
  ·
  <a href="https://www.camemake.eu">camemake.eu</a>
</p>

---

**CameVision Ego Single Sensor** is one global-shutter camera, one IMU, an on-board vision processor with NPU, USB, Wi-Fi 6, BLE, eMMC and battery support.

This repository is the **open demo software** that ships with the product. The live page and IMU HUD run **on the camera**. The host only flashes and opens a browser. USB stays **ADB**.

## Product

| | CameVision Ego Single Sensor · CV-EGO01-SS |
|---|---|
| Cameras | 1 × global shutter (SC233HGS · OG02C10 · MIRA220 · AR0235 colour/mono · OX05B1S · Kaimou GS2.3) |
| IMU | 1 × LSM6DSVQTR (16-bit; ST typical 60 µg/√Hz · 2.8 mdps/√Hz; ±2…16 g / ±125…4000 dps) |
| Compute | On-board vision SoC with integrated NPU |
| Memory | 1 GB RAM |
| Storage | 16 GB eMMC + microSD slot |
| Wired | USB (developer / ADB gadget) · USB-C |
| Wireless | Wi-Fi 6 + BLE |
| Power | USB-C and battery pads |
| Software | This GitHub demo (on-board live page, IMU HUD) |
| Applications | SLAM, VIO, robotics, tool cameras, egocentric and spatial AI |

Maskrom kits in this tree: **SC233HGS** and **AM / MIRA220**. Other shop sensors: [sales@camemake.com](mailto:sales@camemake.com).

Do not flash gen1 serial `0558fa189447bc45`.

## Get started

Flash starts from **Maskrom**. Same path on an empty board and on a board that already has images.

Windows: double-click `CameVision-Single.exe` (bundled Python). Linux: `CameVision-Single`. Installer: http://127.0.0.1:8765/tool.html

```
python tools/cv_single_flash.py --package camevision-single
python tools/cv_single_flash.py --package camevision-mono
python tools/cv_single_page.py
```

1. **USB / Maskrom** — Install USB driver. Hold BOOT, tap RESET, keep BOOT held.
2. **Package** — pick **CameVision Ego Single Sensor · SC233HGS** or **· MIRA220**. Writes loader, env, idblock, U-Boot, boot, userdata, oem, rootfs, then the overlay.
3. **ADB** — live page http://127.0.0.1:8081/ · IMU http://127.0.0.1:8083/

Need: `git lfs pull` after clone (oem / rootfs / userdata). No system Python — `host/python` ships in the tree. Linux extracts `host/linux/python-*.tar.gz` on first run.

Full map: [`FLASH.md`](FLASH.md) · [flash.html](https://camemake.github.io/CameVision-Ego-Single-Sensor/flash.html)
Board nets: [`HARDWARE.md`](HARDWARE.md).

## Repository layout

```
CameVision-Single.exe           Windows installer (bundled Python)
CameVision-Single / .sh         Linux installer
docs/                           GitHub Pages (this product)
  index.html                    Overview
  flash.html                    Maskrom partition map
  datasheet.html                SKU table · IMU precision
tools/                          Flash, overlay, live, IMU, IQ, modules
restore/known-good-20260819-camera-adb/   SPL, env, uboot, oem, rootfs
restore/known-good-20260903-single-camera/  SC233 boot FIT + overlay
restore/release-1.0-mono-mira220-20261014/  MIRA220 boot FIT + overlay
host/python                     Windows Python 3.12 embed
```

PCB schematics stay private.

## Camemake robotic family

CameVision Ego Single Sensor is the **one-camera** board. The same platform is offered as:

| Cameras on the PCB | Role |
|---|---|
| **1 (this product)** | Monocular / tool camera |
| 2 (CameVision Ego) | Hardware-synced stereo |
| 3 | Stereo plus a context camera |
| 5 | Timed array |
| 9 | Near-surround workplace capture |

Read the family on **[Camemake robotic solutions](https://www.camemake.eu/robotic-solutions)**. Email [sales@camemake.com](mailto:sales@camemake.com).

## Documentation

| Page | |
|---|---|
| [Shop](https://www.camemake.eu/shop/camevision-ego-single-sensor-4547) | Camemake shop · CV-EGO01-SS |
| [Product page](https://camemake.github.io/CameVision-Ego-Single-Sensor/) | Public GitHub Pages site |
| [中文](https://camemake.github.io/CameVision-Ego-Single-Sensor/zh/) | Chinese product pages |
| [Get started](https://camemake.github.io/CameVision-Ego-Single-Sensor/start.html) | USB, package, ADB |
| [Flash](https://camemake.github.io/CameVision-Ego-Single-Sensor/flash.html) | Maskrom, partition map |
| [Datasheet](https://camemake.github.io/CameVision-Ego-Single-Sensor/datasheet.html) | SKU table · IMU precision |
| [`FLASH.md`](FLASH.md) | Maskrom from the command line |

## Do not

- Flash this onto CameVision Ego (stereo) or the other way around
- Mix SC233 and MIRA220 images on the same board
- Commit `wpa_camevision.conf` (local Wi-Fi)
- Start a second camera — this product is one sensor, one IMU

© Camemake. CameVision Ego Single Sensor · CV-EGO01-SS.