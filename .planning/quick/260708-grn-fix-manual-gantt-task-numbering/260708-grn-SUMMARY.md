---
status: complete
completed: 2026-07-08
quick_id: 260708-grn
---

# Summary: Fix Manual Gantt Task Numbering

## Outcome

- Manually added Gantt tasks now receive local issue keys like `N-1`, `N-2`, etc. instead of `NEW`.
- Existing local tasks saved with `NEW` are normalized on page load before first render.
- Migrated local task keys are immediately persisted back to local storage.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Generated `gantt.html` inline JavaScript parses in Node.
- Script-level numbering check confirms `NEW` and blank local task keys migrate to sequential `N-x` values.
