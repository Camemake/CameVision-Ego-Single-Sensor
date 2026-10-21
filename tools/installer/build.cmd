@echo off
setlocal
set "CSC=%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" set "CSC=%SystemRoot%\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if not exist "%CSC%" (
  echo csc.exe not found. Need .NET Framework 4.
  exit /b 1
)
set "ROOT=%~dp0..\.."
"%CSC%" /nologo /target:winexe /optimize+ /out:"%ROOT%\CameVision-Single.exe" /r:System.Windows.Forms.dll /r:System.Drawing.dll "%~dp0CameVisionSingleSetup.cs"
if errorlevel 1 exit /b 1
echo wrote CameVision-Single.exe
