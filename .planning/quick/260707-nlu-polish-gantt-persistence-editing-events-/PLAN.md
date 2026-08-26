---
status: in_progress
quick_id: 260707-nlu
date: 2026-07-07
---

# Polish Gantt Editing

## Scope

- Preserve manual task row order after refresh.
- Allow event detail drawers to edit event type/date/summary.
- Add a `进行中` event type with a neutral arrow marker.
- Allow task detail drawers to edit key fields and task bar color from a fixed palette.

## Verification

- Rebuild the generated Gantt page.
- Run Python and generated JavaScript syntax checks.
- Run a browser smoke test for row-order restore, event editing, in-progress event creation, and task color/field persistence.
