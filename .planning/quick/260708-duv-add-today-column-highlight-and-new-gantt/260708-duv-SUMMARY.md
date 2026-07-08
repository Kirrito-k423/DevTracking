---
status: complete
completed: 2026-07-08
quick_id: 260708-duv
---

# Quick Task 260708-duv Summary

## Completed

- Added a light-yellow highlight for today's column across the timeline header and every Gantt row.
- Added new event types:
  - `todo`: neutral hollow-circle marker.
  - `stalled`: grey cross marker for 阻塞.
  - `restart`: yellow circular-arrow marker for 重启.
- Preserved the existing red `blocked` marker as 求助.
- Updated event creation/edit prompts, demo markers, summary counters, marker colors, symbols, sorting order, and type normalization.
- Updated Plane-derived event mapping so `blocked`/blocked state produce grey 阻塞 markers, while `needs-help` still produces red 求助 markers.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Generated Gantt inline JavaScript parsed with Node `vm.Script`.
- Headless browser smoke test confirmed:
  - today's header tick has a light-yellow background and `今天` title;
  - timeline rows receive the today-column highlight;
  - `todo`, `阻塞`, `重启`, and `求助` normalize to their expected event types;
  - new markers render with icons `○`, `×`, and `↻`;
  - summary counters include Todo, Blocked, and Restart counts.
