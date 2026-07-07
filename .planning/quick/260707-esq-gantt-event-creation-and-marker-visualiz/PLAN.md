---
quick_id: 260707-esq
slug: gantt-event-creation-and-marker-visualiz
created: 2026-07-07T02:39:17Z
status: complete
---

# Quick Task: Gantt event creation and marker visualization refinements

## Scope

Refine the generated Demand Hub Gantt page based on visual UAT feedback:

1. Allow long-press event creation anywhere on a task timeline row, including over task bars and existing markers.
2. Support multiple events on the same task and date with a non-overlapping visual layout.
3. Add a local same-day marker demo case for visual testing.
4. Show full task names in the task table instead of the 8-character compact label.
5. Keep marker icons icon-only, opaque, and semantically colored for help/blocker, completed, and milestone.

## Verification

- Rebuild `exports/delivery/gantt.html`.
- Check generated JavaScript compiles.
- Browser-probe long-press event creation over the bar and existing marker.
- Browser-probe same-day multiple event rendering.
- Confirm full task name renders in the task table while the bar remains compact.
- Confirm marker buttons contain no visible label text and are opaque/icon-only.
