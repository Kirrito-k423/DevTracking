---
quick_id: 260707-frp
slug: polish-gantt-same-day-event-stack-visual
created: 2026-07-07T03:21:14Z
status: complete
---

# Quick Task: Polish Gantt same-day event stack visuals

## Scope

Fix the same-day event stack visual polish after UAT feedback:

1. Vertically center collapsed and expanded event stacks in the timeline row.
2. Make the stack background intentional and opaque in both states.
3. Keep collapsed markers centered inside a compact 1.4x visual envelope.
4. Make expanded marker groups visually balanced, not bottom-heavy.
5. Center the collapse button without pushing icons down or sideways.

## Verification

- Rebuild `exports/delivery/gantt.html`.
- Check generated JavaScript compiles.
- Browser-probe collapsed stack vertical center against row center.
- Browser-probe expanded stack vertical center against row center.
- Browser-probe marker centers align with stack center.
- Capture a screenshot for visual inspection.
