---
quick_id: 260707-dwc
slug: gantt
created: 2026-07-07T02:00:24Z
status: in_progress
---

# Quick Task: Gantt readability fixes

## Scope

Adjust the generated Demand Hub Gantt sidecar so it matches operator feedback:

1. Shrink the issue number and allocate more left-table space to useful task names.
2. Render task state in Chinese.
3. Render ranges compactly without year, e.g. `M3~M6`.
4. Keep range text on one line.
5. Remove leading date noise from task bar labels.
6. Render parent-child connectors as square continuous grey dashed lines with stable opacity.
7. Remove the two-tone progress overlay from task bars.

## Verification

- Rebuild `exports/delivery/gantt.json` and `exports/delivery/gantt.html`.
- Check generated data contains useful compact labels without leading `YYYY-MM-DD`.
- Check HTML contains Chinese state/range helpers, square connector path logic, and no progress overlay DOM.
- Confirm the local HTTP page still serves successfully.
