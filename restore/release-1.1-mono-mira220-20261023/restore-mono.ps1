# Push CameVision Mono / MIRA220 overlay (Wi-Fi + BLE + Camemake UVC).
# Deploy stays on ADB. Reboot binds UVC after Wi-Fi is up.
$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
python "$root\tools\cv_single_overlay_deploy_am.py"
