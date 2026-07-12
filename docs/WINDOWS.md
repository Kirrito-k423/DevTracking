# Windows Guide

This repository supports its local Python tools directly on Windows. Plane self-host installation uses its upstream Bash installer through WSL.

## Prerequisites

- Windows 10/11
- Python 3.9 or newer on PATH
- Git
- Docker Desktop with WSL integration when using the self-hosted Plane services

No third-party Python packages are required for the source Gantt server.

## Start the Gantt

From File Explorer, double-click:

```text
portable\gantt\latest\start-windows.bat
```

Or run it from PowerShell:

```powershell
python scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
```

Then open http://127.0.0.1:8091/gantt.html.

The packaged desktop launcher uses %APPDATA%\Plane Demand Hub Gantt for mutable data:

```powershell
python scripts\gantt_app.py
```

## Portable Export and Backup

```powershell
python scripts\export-gantt-portable.py
python scripts\backup-gantt-portable.py --dry-run --branch codex/phase-06-gantt
```

Remove --dry-run only when you intend to commit and push the portable snapshot.

## Plane on Docker Desktop

The upstream Plane installer is Bash-based. Run it through the provided WSL wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File plane-selfhost\setup.ps1 install
```

After Plane is configured and running, the health check and read-only timeline export are native Python commands:

```powershell
python scripts\plane-health.py --url http://localhost:8090
python scripts\export-plane-timeline.py --since 1970-01-01T00:00:00Z --output exports\plane\timeline.jsonl
```

Normal writes still go through the Plane API or controlled connector. The timeline export performs a read-only PostgreSQL transaction.

## Daily Progress Workflows

Always invoke repository Python files through the interpreter on Windows:

```powershell
python scripts\progress-to-plane.py --refresh-timeline "daily progress text"
python scripts\apply-plane-daily-record.py --date YYYY-MM-DD --source-id daily-YYYYMMDD --events-json "[]"
python scripts\bootstrap-plane-visual-constructs.py
```

Set the API key only in the current environment when applying confirmed changes:

```powershell
$env:PLANE_API_KEY = "<your Plane API key>"
python scripts\progress-to-plane.py --apply "confirmed progress text"
```

Do not commit plane-selfhost\plane-app\plane.env, API keys, or generated secrets.
