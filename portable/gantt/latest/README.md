# Portable Gantt Snapshot

This directory is safe to commit. It captures the current Plane Demand Hub Gantt state for another machine.

Exported at: `2026-07-09T06:28:13.779706Z`

Snapshot contents:

- `gantt.html`: portable Gantt page
- `gantt.json`: generated base Gantt data
- `gantt-local-edits.json`: current local edits plus full task/event snapshot
- `manifest.json`: export metadata
- `start-windows.bat` / `start-windows.ps1`: Windows launch helpers

Counts:

- Tasks: 49
- Events: 46

## Windows Quick Start

1. Clone the repository.
2. Double-click `portable\gantt\latest\start-windows.bat`.
3. Open `http://127.0.0.1:8091/gantt.html`.

If double-click is blocked by policy, open PowerShell at the repository root and run:

```powershell
py -3 scripts\serve-delivery-dashboard.py --port 8091
```

## Updating This Snapshot

From the repository root:

```bash
python3 scripts/export-gantt-portable.py
git add portable/gantt/latest
git commit -m "data: update portable gantt snapshot"
git push
```

The Gantt page also has a `导出迁移快照` button that writes this same directory when served through `scripts/serve-delivery-dashboard.py`.
