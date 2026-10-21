@echo off
setlocal
set "CAMEVISION_SINGLE_ROOT=%~dp0"
if "%CAMEVISION_SINGLE_ROOT:~-1%"=="\" set "CAMEVISION_SINGLE_ROOT=%CAMEVISION_SINGLE_ROOT:~0,-1%"
cd /d "%CAMEVISION_SINGLE_ROOT%"
if exist "%CAMEVISION_SINGLE_ROOT%\host\python\python.exe" (
  set "CV_PY=%CAMEVISION_SINGLE_ROOT%\host\python\python.exe"
) else (
  set "CV_PY=python"
)
start "" /min "%CV_PY%" "%CAMEVISION_SINGLE_ROOT%\tools\cv_single_autostart.py" --daemon
start "" /min "%CV_PY%" "%CAMEVISION_SINGLE_ROOT%\tools\cv_single_studio.py"
timeout /t 1 /nobreak >nul
start "" "http://127.0.0.1:8765/tool.html"
if not exist "%CAMEVISION_SINGLE_ROOT%\host\.host-installed" (
  "%CV_PY%" "%CAMEVISION_SINGLE_ROOT%\tools\cv_single_setup.py" --gui
)
endlocal
