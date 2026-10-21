#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_telnet import run
print(run(r"""
echo -n up=; cat /proc/uptime
ip -4 addr show wlan0 | grep inet
echo -n product=; cat /sys/kernel/config/usb_gadget/rockchip/strings/0x409/product 2>/dev/null
echo -n state=; cat /sys/class/udc/21500000.usb/state 2>/dev/null
echo === ps ===
ps | grep -E 'rkaiq_3A|v4l2-ctl|uvc-mjpg|hw_rtsp|isp_grab|mpi_enc|telnetd' | grep -v grep
echo === video ===
ls -l /dev/video13 /dev/mpp_service /dev/video28 2>/dev/null
echo === 3A ===
grep sysctl /userdata/rkaiq.log 2>/dev/null | tail -4
echo === rtsp log ===
tail -c 250 /userdata/hw-rtsp.log 2>/dev/null
""", wait=7))
