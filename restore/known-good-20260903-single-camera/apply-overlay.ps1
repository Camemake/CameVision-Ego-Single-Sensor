# Overlay for known-good-20260903-single-camera. Never overlays gen1 0558fa189447bc45.
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ov = Join-Path $here 'overlay'

$adbCandidates = @(
  'C:\Users\stefa\Downloads\RKDevTool_Release_v3.37\RKDevTool_v3.37_for_window\bin\adb.exe',
  'C:\Users\stefa\Downloads\RKDevTool_Release_v2.84\RKDevTool_Release_v2.84\bin\adb.exe'
)
$adb = $adbCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $adb) { throw 'adb.exe not found' }

$KeepOff = '0558fa189447bc45'

function Get-TargetSerial {
  $raw = & $adb devices
  $sers = @()
  foreach ($line in $raw) {
    if ($line -match '^([0-9a-f]+)\s+device') {
      $sers += $Matches[1]
    }
  }
  $sers = @($sers | Where-Object { $_ -ne $KeepOff })
  if ($sers.Count -eq 0) {
    throw 'No target ADB. Gen1 0558fa189447bc45 is blocked. Connect the Single board.'
  }
  if ($sers.Count -gt 1) {
    throw ("Multiple ADB targets: " + ($sers -join ', '))
  }
  return $sers[0]
}

function PushUnix([string]$src, [string]$dst) {
  if (-not (Test-Path $src)) { throw "missing $src" }
  $tmp = Join-Path $env:TEMP ([IO.Path]::GetFileName($src) + '.unix')
  $bytes = [IO.File]::ReadAllBytes($src)
  if ($src -notmatch '\.(ko|bin|img|json)$') {
    $text = [Text.Encoding]::UTF8.GetString($bytes) -replace "`r`n", "`n" -replace "`r", "`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllText($tmp, $text, $utf8)
    $src = $tmp
  }
  & $adb -s $script:TargetSerial push $src $dst
  if ($LASTEXITCODE -ne 0) { throw "push failed: $dst" }
}

$deadline = (Get-Date).AddSeconds(90)
do {
  Start-Sleep -Seconds 2
  try { $script:TargetSerial = Get-TargetSerial } catch { $script:TargetSerial = $null }
} while (-not $script:TargetSerial -and (Get-Date) -lt $deadline)
if (-not $script:TargetSerial) { throw 'No Single-board ADB (gen1 is blocked).' }
Write-Host "OVERLAY_TARGET=$script:TargetSerial"
& $adb -s $script:TargetSerial shell 'mount -o remount,rw /; mount -o remount,rw /oem; mount -o remount,rw /userdata'

PushUnix (Join-Path $ov 'S20linkmount') /etc/init.d/S20linkmount
PushUnix (Join-Path $ov 'S21appinit') /etc/init.d/S21appinit
PushUnix (Join-Path $ov 'S40network') /etc/init.d/S40network
PushUnix (Join-Path $ov 'S50usbdevice') /etc/init.d/S50usbdevice
PushUnix (Join-Path $ov 'S99camevision') /etc/init.d/S99camevision
PushUnix (Join-Path $ov 'S99ego-stereo.stub') /etc/init.d/S99ego-stereo
PushUnix (Join-Path $ov 'S99ego-stereo.stub') /userdata/S99ego-stereo
PushUnix (Join-Path $ov 'camevision.sh') /etc/profile.d/camevision.sh

PushUnix (Join-Path $ov 'camevision-hw.sh') /userdata/camevision-hw.sh
PushUnix (Join-Path $ov 'camevision-wifi.sh') /userdata/camevision-wifi.sh
PushUnix (Join-Path $ov 'camevision-wifi-m1port.sh') /userdata/camevision-wifi-m1port.sh
PushUnix (Join-Path $ov 'camevision-imu.sh') /userdata/camevision-imu.sh
PushUnix (Join-Path $ov 'camevision-led.sh') /userdata/camevision-led.sh
PushUnix (Join-Path $ov 'camevision-aiq.sh') /userdata/camevision-aiq.sh
PushUnix (Join-Path $ov 'camevision-diag.sh') /userdata/camevision-diag.sh
PushUnix (Join-Path $ov 'imu-live.sh') /userdata/imu-live.sh
PushUnix (Join-Path $ov 'wpa_camevision.conf') /userdata/wpa_camevision.conf
PushUnix (Join-Path $ov 'insmod_wifi.sh') /oem/usr/ko/insmod_wifi.sh
PushUnix (Join-Path $ov 'isp_grab.py') /userdata/isp_grab.py

$tools = Join-Path (Split-Path -Parent (Split-Path -Parent $here)) 'tools'
foreach ($pair in @(
  @('single_live.py', '/userdata/single_live.py'),
  @('single_imu_hud.py', '/userdata/single_imu_hud.py'),
  @('camevision-single.sh', '/userdata/camevision-single.sh'),
  @('S99camevision-single', '/userdata/S99camevision-single'),
  @('S11hwclock', '/userdata/S11hwclock'),
  @('camemake-logo.png', '/userdata/camemake-logo.png')
)) {
  $src = Join-Path $tools $pair[0]
  if (Test-Path $src) { PushUnix $src $pair[1] }
}

$iq = Join-Path $ov 'iqfiles\sc233hgs_efference-sc233hgs_default.json'
& $adb -s $script:TargetSerial shell 'mkdir -p /userdata/iqfiles'
PushUnix $iq /userdata/iqfiles/sc233hgs_efference-sc233hgs_default.json

& $adb -s $script:TargetSerial shell 'mkdir -p /userdata/swt6621_fw /userdata/swt6621-rt52'
Get-ChildItem -LiteralPath (Join-Path $ov 'swt6621_fw') -File | ForEach-Object {
  & $adb -s $script:TargetSerial push $_.FullName "/userdata/swt6621_fw/$($_.Name)"
  if ($LASTEXITCODE -ne 0) { throw "push fw $($_.Name) failed" }
}
Get-ChildItem -LiteralPath (Join-Path $ov 'swt6621-rt52') -Filter '*.ko' | ForEach-Object {
  & $adb -s $script:TargetSerial push $_.FullName "/userdata/swt6621-rt52/$($_.Name)"
  if ($LASTEXITCODE -ne 0) { throw "push ko $($_.Name) failed" }
}

& $adb -s $script:TargetSerial shell @'
chmod 755 /etc/init.d/S20linkmount /etc/init.d/S21appinit /etc/init.d/S40network /etc/init.d/S50usbdevice /etc/init.d/S99camevision /etc/init.d/S99ego-stereo /etc/profile.d/camevision.sh /userdata/camevision-hw.sh /userdata/camevision-wifi.sh /userdata/camevision-wifi-m1port.sh /userdata/camevision-imu.sh /userdata/camevision-led.sh /userdata/camevision-aiq.sh /userdata/camevision-diag.sh /userdata/imu-live.sh /oem/usr/ko/insmod_wifi.sh /userdata/isp_grab.py /userdata/S99ego-stereo /userdata/camevision-single.sh /userdata/S99camevision-single /userdata/S11hwclock
if [ -f /userdata/S99camevision-single ]; then
  cp -f /userdata/S99camevision-single /etc/init.d/S99camevision-single
  cp -f /userdata/S99camevision-single /etc/init.d/S99camevision
  chmod 755 /etc/init.d/S99camevision-single /etc/init.d/S99camevision
fi
if [ -f /userdata/S11hwclock ]; then
  cp -f /userdata/S11hwclock /etc/init.d/S11hwclock
  chmod 755 /etc/init.d/S11hwclock
fi
for p in /proc/[0-9]*; do
  cmd=$(tr "\0" " " < "$p/cmdline" 2>/dev/null)
  case "$cmd" in
    *ego_stereo.py*|*ego_imu_hud.py*|*camevision-stereo.sh*) kill -9 "${p#/proc/}" 2>/dev/null ;;
  esac
done
rm -f /etc/init.d/S99ego-stereo /userdata/S99ego-stereo /userdata/S99ego-stereo.off /userdata/S99ego-stereo.rootfs.off /userdata/uvc-webcam.on /userdata/camevision-stereo.sh /userdata/ego_stereo.py /userdata/ego_imu_hud.py /userdata/ego_cam_sync.py /userdata/ego_calib.html /userdata/libego_stereo.so /userdata/ego-stereo.log /userdata/ego-stereo-boot.log
rm -rf /userdata/__pycache__ /userdata/pylib
sync
'@
Write-Host 'SINGLE_OVERLAY_DONE - ADB gadget was not restarted.'
Write-Host 'grab: v4l2-ctl -d /dev/video13  OR  python3 /userdata/isp_grab.py'
