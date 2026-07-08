@echo off
setlocal
cd /d "%~dp0\..\..\.."
echo Starting Plane Demand Hub Gantt at http://127.0.0.1:8091/gantt.html
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
) else (
  python scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
)
pause
