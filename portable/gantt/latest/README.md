# Portable Gantt Snapshot

This directory is safe to commit. It captures the current Delivery Gantt state for another machine.

Exported at: `2026-08-07T21:00:30.338702Z`

Snapshot contents:

- `gantt.html`: portable Gantt page
- `gantt.json`: generated base Gantt data
- `gantt-local-edits.json`: current local edits plus full task/event snapshot
- `gantt-attachments/`: files bound to tasks and events
- `manifest.json`: export metadata
- `start-windows.bat` / `start-windows.ps1`: Windows launch helpers

Counts:

- Tasks: 105
- Events: 109
- Attachments: 0

## Windows Quick Start

1. Clone the repository.
2. Double-click `portable\gantt\latest\start-windows.bat`.
3. Open `http://127.0.0.1:8090/gantt.html`.

If double-click is blocked by policy, open PowerShell at the repository root and run:

```powershell
python scripts\serve-delivery-dashboard.py --port 8090
```

## Updating This Snapshot

From the repository root:

```powershell
python scripts\export-gantt-portable.py
git add portable/gantt/latest
git commit -m "data: update portable gantt snapshot"
git push
```

The Gantt page also has `导出` and `导入` migration package buttons when served through `scripts/serve-delivery-dashboard.py`.

## Daily GitHub Backup

Use the backup wrapper to choose the newest browser autosave or pushed changeset, regenerate this directory, commit it, and push it to GitHub:

```powershell
python scripts\backup-gantt-portable.py --branch codex/phase-06-gantt
```

See `docs/GANTT-PORTABLE-BACKUP.md` for the scheduled midnight backup details.
