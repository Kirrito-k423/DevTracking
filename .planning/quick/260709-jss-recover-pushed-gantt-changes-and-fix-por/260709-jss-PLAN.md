---
status: ready
created: 2026-07-09
quick_id: 260709-jss
---

# Quick Task 260709-jss: Recover Pushed Gantt Changes and Fix Portable Restore Precedence

## Incident

Refreshing the Gantt page loaded an older portable snapshot and overwrote browser local edits. The latest pushed changeset still exists at `exports/delivery/gantt-local-edits.json`.

## Scope

- Preserve forensic copies of current Gantt edit files.
- Restore `portable/gantt/latest/` from the latest pushed changeset.
- Change Gantt restore precedence so local pushed edits and browser localStorage are not overwritten by an older portable snapshot.
- Verify the page serves the recovered 49-task / 46-event state.

## Verification

- Python compile passes.
- Gantt export regenerates.
- Portable snapshot export uses the latest pushed changeset.
- `/api/gantt-portable/latest` and `/api/gantt-edits/latest` show the recovered counts.
