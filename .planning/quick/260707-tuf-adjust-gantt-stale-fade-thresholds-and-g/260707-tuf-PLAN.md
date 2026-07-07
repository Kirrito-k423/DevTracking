---
status: ready
created: 2026-07-07
quick_id: 260707-tuf
---

# Quick Task 260707-tuf: Adjust Gantt stale fade thresholds and grey weekend holiday headers

## Scope

- Update the generated Gantt view so task bars keep their original color for recent events 0-1 days old, start fading on day 2, and reach the 0.1 opacity floor at day 6 and later.
- Mark Saturday, Sunday, and configured holiday dates in the timeline header with a grey visual treatment.

## Tasks

1. Update `scripts/build-delivery-dashboard.py` Gantt JavaScript constants, fade formula, and header tick class assignment.
2. Add a compact in-page holiday date helper for 2026 China holiday ranges and common fixed-date holidays.
3. Regenerate `exports/delivery/gantt.html` and run syntax/smoke checks.

## Verification

- Python compile passes for the dashboard scripts.
- Gantt export regenerates successfully from existing timeline/progress data.
- Generated inline JavaScript parses.
- Browser smoke check confirms stale opacity thresholds and weekend/holiday tick classes.
