---
quick_id: 260707-g32
slug: gantt-detail-drawer-delete-actions-for-t
created: 2026-07-07T03:34:53Z
status: complete
---

# Quick Task: Gantt detail drawer delete actions

## Scope

Add destructive local-edit actions from the Gantt detail drawer:

1. Task detail drawers show a red delete task button at the bottom.
2. Event detail drawers show a red delete event button at the bottom.
3. Deleting a task removes it from the local Gantt view and keeps child tasks by moving them up one level.
4. Deleting an event removes it from the local Gantt view.
5. Deleted tasks and events persist in `localStorage`.
6. `Push changes` records deleted tasks and deleted events in the changeset.
7. `Reset local edits` restores deleted tasks and events.

## Verification

- Rebuild `exports/delivery/gantt.html`.
- Check generated JavaScript compiles.
- Browser-probe task detail delete button removes the selected task and persists after render.
- Browser-probe event detail delete button removes the selected event and persists after render.
- Browser-probe `Push changes` includes `deleted_tasks` and `deleted_events`.
