---
status: ready
created: 2026-07-09
quick_id: 260709-oki
---

# Quick Task 260709-oki: Task Detail Event Preview And Scoped Report Export

## Scope

- In the task detail drawer, show events from the selected task and its descendants.
- Sort those events by date descending.
- Show enough preview context: date, event type, task title, and summary.
- Add a task-scoped report export button in the task detail drawer.
- The report should include the selected task and descendant tasks.
- Preserve current Gantt snapshot state.

## Verification

- Python compile passes.
- Generated Gantt JavaScript parses.
- Generated HTML contains the task event preview and scoped report export code.
- Portable snapshot remains aligned with the latest local state.
