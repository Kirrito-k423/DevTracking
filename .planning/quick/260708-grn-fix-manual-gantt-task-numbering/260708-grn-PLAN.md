---
status: ready
created: 2026-07-08
quick_id: 260708-grn
---

# Quick Task 260708-grn: Fix Manual Gantt Task Numbering

## Scope

- Replace the hard-coded `NEW` issue key for manually added Gantt tasks.
- Generate stable local task numbers in the form `N-1`, `N-2`, etc.
- Migrate existing local tasks that still have `NEW` so detail drawers and rows show a number instead.

## Tasks

1. Add local task key generation and normalization helpers.
2. Use generated local keys when creating new task bars.
3. Regenerate the Gantt export and verify no new code path emits `issue_key: 'NEW'`.

## Verification

- Python compile passes.
- Gantt export regenerates successfully.
- Generated inline JavaScript parses.
- Script-level check confirms local tasks are assigned numbered keys and `NEW` local tasks are normalized.
