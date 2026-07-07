---
status: complete
quick_id: 260707-kua
date: 2026-07-07
---

# Summary

Added visible Gantt toolbar buttons for creating task bars and events.

## Delivered

- Added `新增任务条` and `新增事件` buttons to the Gantt toolbar.
- Added local task creation with title, optional parent, start date, and end date prompts.
- Added button-driven event creation that selects a task and date, then reuses the existing event type and summary flow.
- Persisted locally created tasks through reloads.
- Added `new_tasks` to the local auditable changeset so created task bars are not mixed into normal task updates.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Node syntax check of generated `exports/delivery/gantt.html`
- Headless Chrome CDP smoke test:
  - new buttons exist
  - creating a task changes task count from 22 to 23
  - creating an event changes event count from 18 to 19
  - reload restores the local task and event
  - `buildChangeset()` reports `new_tasks=1` and `new_events=1`
