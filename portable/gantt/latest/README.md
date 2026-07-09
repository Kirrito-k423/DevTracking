# Portable Gantt Snapshot

This directory is safe to commit. It captures the current Plane Demand Hub Gantt state for another machine.

Exported at: `2026-07-09T06:39:02.578197Z`

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

## Daily GitHub Backup

Use the backup wrapper to choose the newest browser autosave or pushed changeset, regenerate this directory, commit it, and push it to GitHub:

```bash
python3 scripts/backup-gantt-portable.py --branch codex/phase-06-gantt
```

See `docs/GANTT-PORTABLE-BACKUP.md` for the scheduled midnight backup details.
