#!/usr/bin/env python3
import subprocess

ADB = r"C:\Users\stefa\Desktop\Cursor packages\CameVision Single\host\adb.exe"
S = "e4feca993701b30c"


def sh(cmd, t=25):
    r = subprocess.run([ADB, "-s", S, "shell", cmd], capture_output=True, text=True, timeout=t)
    out = (r.stdout or "") + (r.stderr or "")
    print(out, end="" if out.endswith("\n") else "\n")
    return r


sh("mkdir -p /mnt/sdcard; umount /mnt/sdcard 2>/dev/null; mount -t vfat /dev/mmcblk1p1 /mnt/sdcard; echo MOUNT_RC:$?")
sh("df -h /mnt/sdcard /dev/mmcblk1p1 2>/dev/null; ls /mnt/sdcard")
sh("dmesg | tail -30")
sh("ip -4 addr show wlan0")
sh("cat /userdata/wifi-boot.log 2>/dev/null | tail -20")
sh("cat /sys/block/mmcblk1/size; cat /sys/class/mmc_host/mmc1/mmc1:*/type /sys/class/mmc_host/mmc1/mmc1:*/ocr 2>/dev/null")
