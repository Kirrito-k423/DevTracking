---
quick_id: 260707-dwc
slug: gantt
status: complete
completed: 2026-07-07T02:05:00Z
---

# Quick Task Summary: Gantt readability fixes

## Result

The generated Demand Hub Gantt sidecar now uses a denser, more readable task table and cleaner task bars.

## Changes

- Expanded the task table width and gave the task-name column more room.
- Reduced issue-key visual footprint so task names are not crowded out.
- Added compact task labels that strip leading dates and prefer useful content after a colon.
- Changed visible task states to Chinese labels such as `进行中`, `完成`, and `待办`.
- Changed range display to compact month-only text such as `M6～M7`.
- Changed timeline tick labels to short `M/D` style to avoid wrapping.
- Removed the progress overlay that made bars look two-tone.
- Changed parent-child connectors to grouped square grey dashed polylines, one connector network per parent.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py`
- `scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Gantt JSON check: 22 tasks, 18 events, no compact task label starts with `YYYY-`.
- HTML check: Chinese state mapper, month range helper, short tick helper, square connector style, grouped connector logic, and no progress overlay.
- Inline JavaScript syntax check passed with Node `new Function`.
- Local HTTP check: `http://127.0.0.1:8091/gantt.html` returned `200`.

## Notes

Generated files under `exports/` were refreshed locally but remain ignored by git.
