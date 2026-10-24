#!/usr/bin/env python3
from cv_tn import run

print(
    run(
        "echo ===dmesg===; dmesg | grep -iE 'skwbt|hci0|sv6160|nvbin|setup|opcode' | tail -20; "
        "echo ===sys===; cat /sys/class/bluetooth/hci0/address 2>/dev/null; echo; "
        "rfkill list 2>/dev/null; "
        "echo ===btctl===; bluetoothctl power on; bluetoothctl show; "
        "echo BLUEZ_OK",
        wait=10,
    )
)
