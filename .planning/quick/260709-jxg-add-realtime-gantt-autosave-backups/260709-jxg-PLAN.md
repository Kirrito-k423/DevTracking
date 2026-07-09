---
status: ready
created: 2026-07-09
quick_id: 260709-jxg
---

# Quick Task 260709-jxg: Add Realtime Gantt Autosave Backups

## Scope

- Autosave browser Gantt edits to local files after edits, without requiring `Push changes`.
- Keep a rolling timestamped autosave history.
- Restore from autosave before pushed changes and portable snapshot.
- Show visible autosave status in the Gantt toolbar.
- Preserve portable clone behavior.

## Tasks

1. Add local server autosave API and rolling history.
2. Add debounced browser autosave after `persistEdits()`.
3. Update restore precedence: localStorage newer than files, then autosave, then pushed changes, then portable.
4. Regenerate exports and portable snapshot, verify API and UI script behavior.

## Verification

- Python compile passes.
- Gantt HTML JavaScript parses.
- Autosave POST writes `gantt-autosave.json` and `gantt-autosaves/*.json`.
- `/api/gantt-autosave/latest` returns the latest full snapshot.
- Existing recovered pushed/portable state remains 49 tasks / 46 events.
