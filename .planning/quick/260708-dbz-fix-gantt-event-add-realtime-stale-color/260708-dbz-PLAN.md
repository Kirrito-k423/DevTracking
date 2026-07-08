---
status: ready
created: 2026-07-08
quick_id: 260708-dbz
---

# Quick Task 260708-dbz: Fix Gantt event add realtime stale color refresh

## Scope

- Adding an event should immediately refresh the task bar's stale color because the event creation time is new activity.
- The event marker should still render on the selected event date.
- Toolbar-created events should default to today's date rather than the task target/start date.

## Tasks

1. Include event `source_refs.event_time` in Gantt freshness calculations.
2. Change toolbar event date fallback to today.
3. Regenerate and verify the Gantt export with browser checks for live color refresh.

## Verification

- Python compile passes.
- Gantt export regenerates successfully.
- Generated inline JavaScript parses.
- Browser smoke test confirms a stale bar returns to full-color styling after adding a local event, even when the marker date is older.
