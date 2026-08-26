@echo off
setlocal
cd /d "%~dp0\..\..\.."
echo Starting Delivery Gantt at http://127.0.0.1:8090/gantt.html
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8090
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    python scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8090
  ) else (
    echo Python 3 was not found. Install it from https://www.python.org/downloads/windows/ and enable "Add python.exe to PATH".
  )
)
pause
