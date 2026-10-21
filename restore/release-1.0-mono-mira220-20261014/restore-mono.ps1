# Push CameVision Mono / MIRA220 overlay. USB stays ADB.
$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root
python "$root\tools\cv_single_overlay_deploy_am.py"
