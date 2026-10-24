#!/usr/bin/env python3
"""Wait for Maskrom, then flash camevision-mono once."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UT = str(ROOT / "host" / "upgrade_tool.exe")
FLASH = str(ROOT / "tools" / "cv_single_flash.py")


def listing() -> str:
    r = subprocess.run([UT, "ld"], capture_output=True, timeout=20)
    return ((r.stdout or b"") + (r.stderr or b"")).decode("utf-8", "replace")


print("waiting for Maskrom — hold BOOT, tap RESET, keep BOOT held", flush=True)
for i in range(180):
    text = listing()
    if i % 5 == 0:
        print(f"t={i*2}s {text.strip()!r}", flush=True)
    if "Maskrom" in text or "Loader" in text:
        print("FOUND", text, flush=True)
        break
    time.sleep(2)
else:
    print("NO_MASKROM", flush=True)
    sys.exit(2)

r = subprocess.run(
    [sys.executable, FLASH, "--package", "camevision-mono"],
    cwd=str(ROOT),
)
sys.exit(r.returncode)
