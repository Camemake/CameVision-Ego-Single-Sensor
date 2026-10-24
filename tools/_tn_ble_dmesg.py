#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "wc -c /userdata/swt6621_fw/sv6160lite.nvbin /userdata/swt6621_fw/sv6160.nvbin; "
        "echo PATH=$(cat /sys/module/firmware_class/parameters/path); "
        "echo ===dmesg===; dmesg | grep -iE 'sv6160|skwbt|hci0|firmware|nvbin|bt_service|download_nv' | tail -25; "
        "echo ===libfw===; ls -l /lib/firmware/sv6160* 2>/dev/null; mount | grep ' / '; "
        "echo DMESG_OK",
        wait=6,
    )
)
