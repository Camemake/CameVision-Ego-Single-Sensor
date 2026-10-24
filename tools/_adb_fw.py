#!/usr/bin/env python3
import subprocess

SERIAL = "e4feca993701b30c"


def sh(cmd, timeout=20):
    print(">>", cmd)
    p = subprocess.run(
        ["adb", "-s", SERIAL, "shell", cmd],
        capture_output=True,
        timeout=timeout,
    )
    text = ((p.stdout or b"") + (b"\n" + p.stderr if p.stderr else b"")).decode("utf-8", "replace")
    print(text)
    return text


sh("ls -l /userdata/swt6621_fw /lib/firmware/sv6160lite.nvbin /lib/firmware/SWT6621S_NV_SDIO*.bin 2>/dev/null")
sh("wc -c /userdata/swt6621_fw/sv6160lite.nvbin /userdata/swt6621_fw/SWT6621S_NV_SDIO_SHARE.bin /lib/firmware/sv6160lite.nvbin 2>/dev/null")
