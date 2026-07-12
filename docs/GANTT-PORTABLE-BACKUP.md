# Gantt Portable GitHub Backup

The Gantt page stores lightweight browser edits locally, then exports a clone-ready snapshot under `portable/gantt/latest/`.

Daily backup is handled by `scripts/backup-gantt-portable.py`.

## What It Saves

- Latest browser autosave: `exports/delivery/gantt-autosave.json`
- Explicit pushed edits: `exports/delivery/gantt-local-edits.json`
- Portable fallback: `portable/gantt/latest/gantt-local-edits.json`

The backup script chooses the newest valid full snapshot in this order when timestamps tie:

1. realtime autosave
2. pushed changes
3. existing portable snapshot

It then regenerates `portable/gantt/latest/`, commits only that directory, and pushes the current branch to GitHub.

## Manual Run

From the repository root:

```powershell
python scripts\backup-gantt-portable.py --branch codex/phase-06-gantt
```

For a local test without Git commit or push:

```powershell
python scripts\backup-gantt-portable.py --dry-run --branch codex/phase-06-gantt
```

If GitHub is unreachable from China without a proxy, the script defaults Git push to `http://127.0.0.1:7890` for GitHub remotes.

## Daily Automation

Codex has a local cron automation named `Daily Gantt portable GitHub backup`.

Automation id: `daily-gantt-portable-github-backup`

It runs every day at local midnight and calls:

```bash
python scripts/backup-gantt-portable.py --branch codex/phase-06-gantt
```

## Restore On Another Machine

1. Clone the GitHub repository.
2. Start the local dashboard server:

```powershell
python scripts\serve-delivery-dashboard.py --port 8091
```

3. Open `http://127.0.0.1:8091/gantt.html`.

The page loads `portable/gantt/latest/gantt-local-edits.json` when no newer local autosave or pushed edits exist on that machine.
