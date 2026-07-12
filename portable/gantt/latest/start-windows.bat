@echo off
setlocal
cd /d "%~dp0\..\..\.."
echo Starting Plane Demand Hub Gantt at http://127.0.0.1:8091/gantt.html
where py >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    python scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
  ) else (
    echo Python 3 was not found. Install it from https://www.python.org/downloads/windows/ and enable "Add python.exe to PATH".
  )
)
pause
