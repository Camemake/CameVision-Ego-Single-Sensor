#!/usr/bin/env python3
"""Carve factory M1 Wi-Fi init + firmware/module names from system_a.img."""
from __future__ import annotations

from pathlib import Path

IMG = Path(r"C:\Users\stefa\Desktop\CameVision Single\build\m1-donor\system_a.img")
OUT = Path(r"C:\Users\stefa\Desktop\CameVision Single\build\m1-donor\extracted")


def as_text(raw: bytes) -> str:
    out = []
    for b in raw:
        if b == 0:
            out.append("\n")
        elif b == 0x0A:
            out.append("\n")
        elif 32 <= b < 127 or b in (9, 13):
            out.append(chr(b))
        else:
            out.append("\n")
    text = "".join(out)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip() + "\n"


def main() -> int:
    data = IMG.read_bytes()
    OUT.mkdir(parents=True, exist_ok=True)

    # S25 body was previously seen at ~0x39130
    start = data.find(b"KO=/ko")
    # prefer the VS6621 start() block
    vs = data.find(b"VS6621 SDIO ID 1FFE:6621")
    print(f"KO=/ko {start:#x}" if start >= 0 else "KO=/ko missing")
    print(f"VS6621 marker {vs:#x}" if vs >= 0 else "VS6621 missing")

    if vs >= 0:
        lo = max(0, vs - 800)
        hi = min(len(data), vs + 4500)
        (OUT / "S25_efference_wlan.carve.sh").write_text(as_text(data[lo:hi]), encoding="utf-8")
        print("wrote S25_efference_wlan.carve.sh")

    for key, name, back, fwd in (
        (b"S99_efference_wifi", "S99_efference_wifi.carve.sh", 200, 2500),
        (b"S98_efference_capture_wifi", "S98_efference_capture_wifi.carve.sh", 200, 2000),
        (b"S60_efference_ota_bled", "S60_efference_ota_bled.carve.sh", 200, 2000),
        (b"SWT6621S_NV_SDIO_ALONE.bin", "firmware_note.carve.txt", 300, 400),
    ):
        i = data.find(key)
        print(f"{name} {hex(i) if i>=0 else None}")
        if i >= 0:
            (OUT / name).write_text(as_text(data[i - back : i + fwd]), encoding="utf-8")

    # unique firmware basenames near Seekwave
    names = set()
    needle = b"SWT6621"
    pos = 0
    while True:
        i = data.find(needle, pos)
        if i < 0:
            break
        j = i
        while j > 0 and data[j - 1] in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./-":
            j -= 1
        k = i
        while k < len(data) and data[k] in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_./-":
            k += 1
        names.add(data[j:k].decode("ascii", "ignore"))
        pos = i + 1
        if len(names) > 80:
            break
    (OUT / "seekwave_names.txt").write_text("\n".join(sorted(names)) + "\n", encoding="utf-8")
    print("seekwave names", len(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
