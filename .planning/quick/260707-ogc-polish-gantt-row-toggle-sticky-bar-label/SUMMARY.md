---
status: complete
quick_id: 260707-ogc
date: 2026-07-07
---

# Summary

Polished Gantt row interactions for left-side toggling, sticky task bar labels, and inline Owner editing.

## Delivered

- Left task table rows now support click-to-collapse/expand from the task name, State, and Range areas.
- Owner cells are editable by double-clicking without triggering row collapse.
- Task bar labels use sticky positioning and a scroll fallback so text stays near the visible front of the bar while remaining inside the bar.
- Owner edits are persisted locally and included in `task_changes.owner` during `Push changes`.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Node syntax check of generated `exports/delivery/gantt.html`
- Headless Chrome CDP smoke test:
  - clicking the left task name area collapses and expands child rows
  - double-clicking Owner updates the cell and changeset
  - task bar label CSS is `position: sticky` and remains inside the bar
