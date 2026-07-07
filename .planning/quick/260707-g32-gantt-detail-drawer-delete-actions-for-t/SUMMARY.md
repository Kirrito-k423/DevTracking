---
quick_id: 260707-g32
slug: gantt-detail-drawer-delete-actions-for-t
status: complete
completed: 2026-07-07T03:39:00Z
---

# Quick Task Summary: Gantt detail drawer delete actions

## Result

Task and event detail drawers now include red delete actions. Deletions are local edits, persist in `localStorage`, and are included in the `Push changes` changeset.

## Changes

- Added a danger section at the bottom of the detail drawer.
- Task detail drawers now show `删除任务`.
- Event detail drawers now show `删除事件`.
- Deleting a task removes the selected task from the local Gantt view and moves its children up one level.
- Deleting an event removes only that event from the local Gantt view.
- Persisted local edit payloads now include `deleted_task_ids` and `deleted_event_ids`.
- Changesets now include `deleted_tasks` and `deleted_events`.
- `Reset local edits` still restores deleted tasks and events.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Inline JavaScript syntax check passed with Node `new Function`.
- Local HTTP check: `http://127.0.0.1:8091/gantt.html` returned `200`.
- Browser probe passed: deleting one event changed event count from `18` to `17`; deleting one task changed task count from `22` to `21`.
- Browser probe confirmed deleted task/event IDs persist through `localStorage` restore and appear in `buildChangeset()` as `deleted_tasks=1` and `deleted_events=1`.
- Visual screenshot written to `/tmp/gantt-delete-drawer.png`.

## Notes

Existing ignored changeset files under `exports/delivery/` were left untouched.
