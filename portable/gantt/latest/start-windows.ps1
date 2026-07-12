$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $Root
Write-Host "Starting Plane Demand Hub Gantt at http://127.0.0.1:8091/gantt.html"
if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
} else {
  $Python = Get-Command python -ErrorAction SilentlyContinue
  if (-not $Python) {
    throw 'Python 3 was not found. Install it from https://www.python.org/downloads/windows/ and enable "Add python.exe to PATH".'
  }
  & $Python.Source scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
}
