#!/usr/bin/env python3
"""Disassemble Rockchip MMC identify/clock functions from tools/_kernel.bin."""
from pathlib import Path

STEXT = 0xFFFFFFC008010000
SYMS = {
    "mmc_set_ios": 0xFFFFFFC00859E874,
    "mmc_go_idle": 0xFFFFFFC0085A58D0,
    "mmc_sd_init_card": 0xFFFFFFC0085A7C98,
    "__mmc_send_if_cond": 0xFFFFFFC0085A8784,
    "mmc_send_if_cond": 0xFFFFFFC0085A89F8,
    "dw_mci_setup_bus": 0xFFFFFFC0085B3840,
    "dw_mci_set_ios": 0xFFFFFFC0085B6A50,
    "dw_mci_rk3288_set_ios": 0xFFFFFFC0085B726C,
    "dw_mci_rk3288_parse_dt": 0xFFFFFFC0085B7A40,
    "mmc_sd_get_cid": 0xFFFFFFC0085A752C,
}


def dec(w):
    return (
        f"{(w >> 0) & 31:2d} {(w >> 5) & 31:2d} {(w >> 10) & 31:2d} "
        f"{(w >> 16) & 31:2d} op={(w >> 21) & 0x7FF:03x} {w:08x}"
    )


def main():
    data = Path(__file__).resolve().parent.joinpath("_kernel.bin").read_bytes()
    for name, va in SYMS.items():
        off = va - STEXT
        print(f"\n===== {name} {va:x} off={off:x} =====")
        blob = data[off : off + 96]
        for i in range(0, len(blob), 4):
            w = int.from_bytes(blob[i : i + 4], "little")
            print(f"  {va+i:x}: {w:08x}")


if __name__ == "__main__":
    main()
