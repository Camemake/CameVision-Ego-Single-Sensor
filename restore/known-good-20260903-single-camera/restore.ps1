# Maskrom restore: current CameVision Single camera point (2026-09-03).
# ADB + Wi-Fi + SC233HGS. No Ego, no UVC. Never flashes gen1 0558fa189447bc45.
# Hold BOOT, tap RESET, then run this. Release BOOT after it prints rd.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent (Split-Path -Parent $here)
$kg = Join-Path $repo 'restore\known-good-20260819-camera-adb'
$utCandidates = @(
  (Join-Path $repo 'host\upgrade_tool.exe'),
  'C:\Users\stefa\Downloads\SocToolKit\bin\windows\upgrade_tool.exe'
)
$adbCandidates = @(
  (Join-Path $repo 'host\adb.exe'),
  'C:\Users\stefa\Downloads\RKDevTool_Release_v3.37\RKDevTool_v3.37_for_window\bin\adb.exe'
)
$ut = $utCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$adb = $adbCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$loader = Join-Path $kg 'rv1126b_spl_loader_k4a8g.bin'
$boot = Join-Path $here 'camevision_boot.img'
$userdataCandidates = @(
  (Join-Path $repo 'firmware\aura-stock\Luckfox_Aura_Buildroot_eMMC_260606\userdata.img'),
  'C:\Users\stefa\Desktop\CameVision Single\firmware\aura-stock\Luckfox_Aura_Buildroot_eMMC_260606\userdata.img'
)
$userdata = $userdataCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not (Test-Path $boot)) { throw 'missing camevision_boot.img' }
if (-not (Test-Path $ut)) { throw 'missing upgrade_tool' }
if (-not (Test-Path $userdata)) { throw 'missing userdata.img' }

Write-Host '=== ld ==='
$ld = & $ut ld 2>&1 | Out-String
Write-Host $ld
if ($ld -notmatch 'Maskrom|Loader|rockchip') { throw 'No Rockusb. Hold BOOT, tap RESET, then re-run.' }

$loaderUp = ($ld -match 'SerialNo=rockchip') -or ($ld -match 'SerialNo=0\s')
if ($ld -match 'Maskrom' -and -not $loaderUp) {
    Write-Host '=== db loader once ==='
    & $ut db $loader
    if ($LASTEXITCODE -ne 0) { throw 'db failed' }
    Start-Sleep -Seconds 2
    Write-Host (& $ut ld 2>&1 | Out-String)
} else {
    Write-Host '=== skip db ==='
}

$writes = @(
    @{ lba = '0x0';      file = (Join-Path $kg 'env.img') },
    @{ lba = '0x40';     file = (Join-Path $kg 'idblock.img') },
    @{ lba = '0x440';    file = (Join-Path $kg 'uboot.img') },
    @{ lba = '0x2440';   file = $boot },
    @{ lba = '0x7C40';   file = $userdata },
    @{ lba = '0x207C40'; file = (Join-Path $kg 'oem_noko.img') },
    @{ lba = '0x607C40'; file = (Join-Path $kg 'rootfs_bootstable.img') }
)
foreach ($w in $writes) {
    if (-not (Test-Path $w.file)) { throw "missing $($w.file)" }
    Write-Host ("=== wl {0} {1} ===" -f $w.lba, [IO.Path]::GetFileName($w.file))
    & $ut wl $w.lba $w.file
    if ($LASTEXITCODE -ne 0) { throw "wl failed $($w.file)" }
}

Write-Host '=== rd - RELEASE BOOT, tap RESET only if USB stays empty ==='
Start-Sleep -Seconds 3
& $ut rd
Write-Host 'FLASH_DONE - waiting for ADB (2207:0006)'

$ok = $false
$deadline = (Get-Date).AddSeconds(120)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 4
    $devs = & $adb devices 2>&1 | Out-String
    $ld2 = & $ut ld 2>&1 | Out-String
    Write-Host ("--- {0:HH:mm:ss} ---" -f (Get-Date))
    Write-Host $devs.Trim()
    if ($devs -match '(?m)^(?!0558fa189447bc45)([0-9a-f]+)\s+device') {
        $ok = $true
        Write-Host ("NEW_BOARD_ADB=" + $Matches[1])
        break
    }
    if ($devs -match '0558fa189447bc45') {
        Write-Host 'gen1 ADB is present and will not be overlaid - waiting for the new board'
    }
    if ($ld2 -match 'Maskrom' -and $ld2 -notmatch 'SerialNo=0') {
        Write-Host 'STILL MASKROM - release BOOT completely, tap RESET only'
    }
}
if (-not $ok) {
    Write-Host 'ADB not up yet. Unplug USB-C, plug in, tap RESET, then run apply-overlay.ps1'
    exit 2
}

Write-Host '=== apply overlay ==='
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'apply-overlay.ps1')
if ($LASTEXITCODE -ne 0) { throw 'overlay failed' }

Write-Host 'SINGLE_CAMERA_READY'
Write-Host 'USB is ADB only. Camera: v4l2-ctl on /dev/video13'
Write-Host 'diag: adb shell /userdata/camevision-diag.sh'
