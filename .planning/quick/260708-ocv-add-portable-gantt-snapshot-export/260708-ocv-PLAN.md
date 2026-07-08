---
status: ready
created: 2026-07-08
quick_id: 260708-ocv
---

# Quick Task 260708-ocv: Add Portable Gantt Snapshot Export

## Scope

- Add a commit-friendly portable Gantt snapshot under `portable/gantt/latest/`.
- Add a CLI command: `python3 scripts/export-gantt-portable.py`.
- Add a Gantt toolbar button that writes the portable snapshot through the local server.
- Make the Gantt page prefer the portable snapshot, then fall back to browser localStorage.
- Make Windows clone startup easy with a portable README and launch script.

## Tasks

1. Implement portable snapshot export script and server API routes.
2. Update the Gantt page to load portable snapshots and add a one-click export button.
3. Generate the current portable snapshot, verify local and clone-style startup paths, then commit and push.

## Verification

- Python compile passes.
- Gantt export regenerates successfully.
- Portable export script writes `portable/gantt/latest/`.
- Generated Gantt JavaScript parses.
- Server returns `/api/gantt-portable/latest` and `/gantt.html`.
