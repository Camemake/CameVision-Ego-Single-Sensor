# Hardware

CameVision one-camera boards. SoC is Rockchip RV1126B. USB gadget is ADB
only on this product path.

## CameVision Single — SC233HGS

| Net | Use |
|---|---|
| CSI RX0, 4-lane | SC233HGS |
| I2C3 `@0x30` | Sensor CCI |
| CAM_PWDN GPIO4_A6 | **ACTIVE_LOW** (M1 polarity). Do not flip. |
| ISP | `rkisp_mainpath` = `/dev/video13` NV12 1920×1200 |
| IMU | LSM6 on **SPI1**. Do not enable SPI1 CSN1 (that pad is CAM_PWDN). |
| IQ | `sc233hgs_efference-sc233hgs_default.json` |
| Clock | `clk_mipi0_out2io` on CAM_CLK0_OUT |

## CameVision Mono — MIRA220 (CameVisionMono_OV V0.3)

| Net | SoC | Use |
|---|---|---|
| I2C3 SCL/SDA | GPIO4_A4/A5 | MIRA220 CCI `@0x54` (CCI_ADDR0/1 GND) |
| MIPI CSI RX0 CLK/D0/D1 | CSI0 | 2-lane RAW10 |
| MIPI_RX0_MCLK | CAM_CLK0_OUT | 38.4 MHz in `S10mira220` |
| PWR_EN_2.5V_CAM0 | GPIO0_B0 | AVDD 2.5 V first |
| PWR_EN_1.35V_CAM0 | GPIO0_B2 | DVDD 1.35 V |
| PWR_EN_1.8V_CAM0 | GPIO0_B1 | DOVDD 1.8 V |
| CAM0_RST | GPIO6_A7 | ARST_B, pull-up, release high |
| CAM0_ILU_TRIG | GPIO4_A3 | illuminator, **not** PWDN |
| SPI0 CLK/CS/MISO/MOSI | GPIO5_A6/A3/A5/A4 | LSM6DSV320XTR |
| IMU0_INT1 | GPIO5_B5 | DRDY |

Power order: **2.5 V → 1.35 V → 1.8 V → RST**. CIF only (`/dev/video1`).
No rkaiq 3A on this path.

Live color path (same as Ego AM CAM0):

- Capture 1600×1400 compact RAW10 GRBG, stride 2048
- AWB LUTs R×1.90 G×1.38 B×3.06, black-10
- `libsingle_color.so` `ego_raw10_color_nv12`, 90° CCW → 1400×1600
- Exposure 3600, vblank 2695, VSTART 0 (re-applied after stream-on)

The mira220 driver rewrites VSTART=64 and EXP=1000 on STREAMON. The live
page writes the Ego window/exposure after mmap and every few seconds.

IQ: `mira220_camevision-mira220_default.json`.

First Mono boards may boot the Ego AM FIT (dual MIRA220 DTB). CAM1 is
unused. A CAM0-only FIT is the later cleanup (`device-tree/README-AM.md`).

## Shared

| | |
|---|---|
| SoC | RV1126B, kernel `6.1.141-rt52` PREEMPT_RT |
| RAM / eMMC | 1 GB DDR4 / 16 GB |
| Wi-Fi | VS6621 on mmc2 |
| USB | ADB developer gadget. `upgrade_tool db` once per Maskrom session. |

Do not copy Ego stereo, FSYNC, dual IMU, or CAM1 i2c-gpio into this tree.
