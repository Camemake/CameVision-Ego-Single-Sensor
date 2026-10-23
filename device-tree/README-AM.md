# CameVision Mono — MIRA220 device tree notes

Authoritative schematic: `d:\CameVision Mono AM.pdf` (CameVisionMono_OV V0.3, 2026-09-12).

First boards boot the Ego AM FIT (`camevision_boot_ego_am.img`) so CAM0 I2C
`@0x54`, 2-lane CSI RX0 and SPI0 IMU0 come up. CAM1 in that FIT has no
sensor and is ignored. A CAM0-only FIT from
`rv1126b-camevision-single-am.dts` is the later cleanup.

| Net | SoC | Use |
|---|---|---|
| I2C3_SCL/SDA_CAM | GPIO4_A4/A5 | MIRA220 CCI `@0x54` |
| MIPI CSI RX0 CLK/D0/D1 | CSI0 | 2-lane RAW10, 750 MHz |
| MIPI_RX0_MCLK | CAM_CLK0_OUT | 38.4 MHz in `S10mira220` |
| PWR_EN_2.5V_CAM0 | GPIO0_B0 | AVDD 2.5 V first |
| PWR_EN_1.35V_CAM0 | GPIO0_B2 | DVDD 1.35 V |
| PWR_EN_1.8V_CAM0 | GPIO0_B1 | DOVDD 1.8 V |
| CAM0_RST | GPIO6_A7 | ARST_B, pull-up, release high |
| CAM0_ILU_TRIG | GPIO4_A3 | illuminator, **not** PWDN |
| SPI0 CLK/CS/MISO/MOSI | GPIO5_A6/A3/A5/A4 | LSM6DSV320XTR |
| IMU0_INT1 | GPIO5_B5 | DRDY |
| SDMMC0 CLK/CMD/D0-D3 | GPIO2_A4/A5/A0-A3 | microSD, 3.3 V I/O |
| vcc3v3_sd | GPIO3_B4 enable from vcc3v3_sys | card VDD 3.3 V (node still named vcc1v8-sd) |

microSD is `sdmmc0` (`mmc@21d60000`). Program **3.3 V / 3.3 V** (`vmmc` + `vqmmc`). Do not use `vcc_1v8` or `sd-uhs-*` — those switch card I/O to 1.8 V and the card never enumerates. Do not mux `SDMMC0_DET` (GPIO0_A5, green LED) or `SDMMC0_PWREN` (GPIO0_B2, CAM0 DVDD). Use `broken-cd`.

Do not copy Ego's 2.8 / 1.2 / 1.8 V regulator names onto this BOM.
Do not copy Ego CAM0_PWDN on GPIO4_A3.
