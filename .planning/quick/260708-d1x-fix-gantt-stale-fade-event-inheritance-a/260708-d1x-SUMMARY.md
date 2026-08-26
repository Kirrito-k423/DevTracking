---
status: complete
completed: 2026-07-08
quick_id: 260708-d1x
---

# Quick Task 260708-d1x Summary

## Completed

- Parent task stale fading now walks the task subtree, so child and deeper descendant events count as activity for the parent task bar.
- Event marker rendering remains row-local: child events affect parent color freshness but are not duplicated visually onto the parent row.
- Local task bars created from the HTML add button now participate in stale fading even without explicit event markers by falling back to their start date.
- `local_task_created` source refs are no longer treated as freshness events, so creating an old-range local task no longer masks stale fading.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Generated Gantt inline JavaScript parsed with Node `vm.Script`.
- Headless browser smoke test confirmed:
  - parent opacity stays `1` when a child task has an event today;
  - parent opacity reaches `0.1` when the child task's latest event is 6 days old;
  - a local task with no explicit event and a start date 6 days old reaches `0.1`;
  - a local task with an explicit event today stays at opacity `1`.
