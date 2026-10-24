#!/bin/sh
U=/sys/kernel/config/usb_gadget/rockchip/functions/uvc.gs1
echo FRAMES
ls "$U/streaming/mjpeg/m"
echo INTERVAL
cat "$U/streaming/mjpeg/m/1400_1600p/dwFrameInterval" 2>/dev/null
echo LIVE
tail -20 /userdata/single-live.log
echo BRIDGE
tail -25 /userdata/cv-uvc-bridge.log
echo CTL
cat /tmp/camevision-uvc-ctl.json
echo PS
ps | grep -E 'single_live|uvc-bridge'
