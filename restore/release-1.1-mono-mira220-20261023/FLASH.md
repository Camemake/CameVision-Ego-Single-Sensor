# CameVision Mono / MIRA220 · Maskrom flash

Empty Mono AM board. Writes the wifi-pad boot FIT so VS6621 Wi-Fi + BLE
come up. After first boot, Camemake UVC binds when `wlan0` has an address.

```
python tools/cv_single_flash.py --package camevision-mono
```

Board already running ADB: `restore-mono.ps1` or
`python tools/cv_single_overlay_deploy_am.py`. Then reboot (or run
`/userdata/_lock_uvc_safe.sh` over telnet) for the webcam gadget.
