---
quick_id: 260707-ea2
slug: gantt-sidecar-local-interaction-editing
created: 2026-07-07T02:16:52Z
status: complete
---

# Quick Task: Gantt local interaction editing

## Scope

Make the generated Demand Hub Gantt page locally interactive without writing to Plane:

1. Long-press a row to drag it. The row floats with the pointer.
2. Dropping between rows reorders the task; dropping onto a task makes it a child and opens that parent.
3. Show a gray placeholder gap while dragging, and visually enlarge a parent target.
4. Drag either edge of a task bar to change start or target date.
5. Double-click task text or a task bar label to rename the task.
6. Long-press an empty day position on a row to add a blocked, completed, or milestone marker.
7. Timeline bounds should come from first/last task dates with one month of padding.
8. Changes persist in browser localStorage and remain local-only.

## Verification

- Rebuild `exports/delivery/gantt.html`.
- Check generated JavaScript compiles.
- Check HTML contains local edit persistence, row drag, bar resize, rename, event creation, and one-month timeline padding code paths.
- Confirm local HTTP page still serves.
