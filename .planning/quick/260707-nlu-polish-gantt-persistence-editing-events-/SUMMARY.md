---
status: complete
quick_id: 260707-nlu
date: 2026-07-07
---

# Summary

Polished Gantt editing around row order persistence, event editing, in-progress markers, and task field/color editing.

## Delivered

- Preserved manually adjusted task row order after refresh by restoring tasks in saved local order.
- Added `order_index` to changesets so sibling reordering is auditable.
- Added event editing from the detail drawer and double-click marker shortcut.
- Added `进行中` event type with a neutral arrow marker.
- Added task field editing for title, owner, state, progress, start/end dates, blocker, next action, labels, and modules.
- Added task bar color editing with the requested 16-color palette.
- Added `event_changes` and expanded `task_changes` so modified existing events and task fields are included in `Push changes`.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Node syntax check of generated `exports/delivery/gantt.html`
- Headless Chrome CDP smoke test:
  - manual task order survives reload
  - event type/name edit is persisted and appears in `event_changes`
  - `进行中` event creates `.marker.in_progress`
  - task fields and color persist through reload
