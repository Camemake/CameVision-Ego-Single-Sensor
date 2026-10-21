$adb = 'C:\Users\stefa\Downloads\RKDevTool_Release_v3.37\RKDevTool_v3.37_for_window\bin\adb.exe'
$ut = 'C:\Users\stefa\Downloads\SocToolKit\bin\windows\upgrade_tool.exe'
$deadline = (Get-Date).AddSeconds(75)
while ((Get-Date) -lt $deadline) {
  $devs = & $adb devices 2>&1 | Out-String
  $ld = & $ut ld 2>&1 | Out-String
  $pnp = @(Get-PnpDevice | Where-Object { $_.Present -and $_.InstanceId -match 'VID_2207' } | ForEach-Object { "$($_.Status) $($_.FriendlyName)" })
  Write-Host ("--- {0:HH:mm:ss} ---" -f (Get-Date))
  Write-Host $devs.Trim()
  Write-Host $ld.Trim()
  Write-Host ($pnp -join ' | ')
  if ($devs -match '(?m)^[0-9a-f]+\s+device') { Write-Host 'ADB_UP'; break }
  Start-Sleep -Seconds 5
}
