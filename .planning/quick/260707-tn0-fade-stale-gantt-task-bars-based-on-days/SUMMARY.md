---
status: complete
quick_id: 260707-tn0
date: 2026-07-07
---

# Summary

Added stale-progress visual fading for Gantt task bars.

## Delivered

- Task bars now fade based on days since the latest task event.
- The latest event source includes explicit event markers first and falls back to Plane/source refs when no marker exists.
- Bars stay full color for 0-5 days.
- At 6 days, the bar color starts fading.
- At 30 days and beyond, the bar background opacity is clamped to 0.1.
- Task labels and event markers remain readable; only the task bar background color is faded.
- Bar hover titles include the number of days since the latest event.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Node syntax check of generated `exports/delivery/gantt.html`
- Headless Chrome CDP smoke test:
  - fresh event opacity is `1`
  - 6-day-old event opacity is lower than fresh
  - 30-day-old event opacity is clamped to `0.1`
  - rendered bar background uses `rgba(..., 0.1)` for a 30-day stale task
