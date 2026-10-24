#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "echo ===net===; ip -4 addr show wlan0 | head -3; "
        "echo ===hci===; hciconfig -a hci0; "
        "echo ===bt===; cat /proc/skwsdio/bt_service; echo; "
        "echo ===fwpath===; cat /sys/module/firmware_class/parameters/path; echo; "
        "echo ===fw===; wc -c /userdata/swt6621_fw/sv6160lite.nvbin /userdata/swt6621_fw/SWT6621S_NV_SDIO_SHARE.bin /userdata/swt6621_fw/SWT6621S_NV_SDIO.bin; "
        "ls -l /lib/firmware/sv6160lite.nvbin /lib/firmware 2>/dev/null | head -8; "
        "echo ===mod===; lsmod | grep -E 'skw|swt|wifi|bt'; "
        "echo ===sdio===; ls /sys/bus/sdio/devices; "
        "echo ===dmesg===; dmesg | grep -iE 'sv6160|skwbt|hci0|firmware|nvbin|BT SERVICE|bt_service' | tail -20; "
        "echo ===ps===; ps | grep -E 'bluetooth|camevision' | grep -v grep; "
        "echo DIAG_DONE",
        wait=8,
    )
)
