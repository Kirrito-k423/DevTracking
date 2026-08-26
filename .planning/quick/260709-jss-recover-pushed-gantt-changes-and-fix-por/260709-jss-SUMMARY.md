---
status: complete
completed: 2026-07-09
quick_id: 260709-jss
---

# Summary: Recover Pushed Gantt Changes and Fix Portable Restore Precedence

## Incident Result

- Recovered the latest pushed changeset from `exports/delivery/gantt-local-edits.json`.
- Restored `portable/gantt/latest/` to the recovered 49-task / 46-event state.
- Preserved forensic copies under `.planning/recovery/gantt-loss-20260709T141427/` on the local machine.

## Root Cause

The Gantt page loaded `portable/gantt/latest` before checking local pushed edits. Because the portable snapshot was older in content, refresh restored a 40-task / 29-event snapshot and then persisted it into browser localStorage.

## Fix

- Gantt startup now checks browser localStorage, `/api/gantt-edits/latest`, and `/api/gantt-portable/latest`.
- Explicit `Push changes` data wins over portable snapshots.
- Browser localStorage can win only when it has a `saved_at` timestamp newer than pushed changes.
- `persistEdits()` now records `saved_at`.
- `.planning/recovery/` is ignored so incident evidence is kept locally but not accidentally pushed.

## Verification

- Python compile passed.
- Gantt export regenerated.
- Portable snapshot regenerated from `exports/delivery/gantt-local-edits.json`.
- `exports/delivery/gantt-local-edits.json`: 49 tasks / 46 events.
- `portable/gantt/latest/gantt-local-edits.json`: 49 tasks / 46 events.
- `/api/gantt-edits/latest`: 49 tasks / 46 events.
- `/api/gantt-portable/latest`: 49 tasks / 46 events.
