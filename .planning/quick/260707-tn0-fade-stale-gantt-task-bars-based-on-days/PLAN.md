---
status: in_progress
quick_id: 260707-tn0
date: 2026-07-07
---

# Fade Stale Gantt Task Bars

## Scope

- Fade task bar background colors based on days since the task's latest event marker.
- Keep task labels and event markers readable while the bar color fades.
- Start fading when the latest event is at least 6 days old.
- Clamp the minimum background opacity to 0.1 for very stale tasks.

## Verification

- Rebuild the generated Gantt page.
- Run Python and generated JavaScript syntax checks.
- Run a browser smoke test for opacity calculation and rendered bar styling.
