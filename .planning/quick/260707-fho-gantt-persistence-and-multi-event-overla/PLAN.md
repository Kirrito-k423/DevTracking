---
quick_id: 260707-fho
slug: gantt-persistence-and-multi-event-overla
created: 2026-07-07T03:09:12Z
status: complete
---

# Quick Task: Gantt persistence and multi-event overlap interaction

## Scope

Refine the generated Demand Hub Gantt page after UAT feedback:

1. Make it explicit that current page edits do not silently sync to Plane.
2. Add a `Push changes` path that persists browser edits as an auditable local changeset.
3. Keep Plane mutation out of the static page; later Plane writes must go through a controlled API writer.
4. Change same-day multiple-event display so collapsed markers stay within one date cell.
5. Collapse multiple same-day markers by default into overlapped icons spanning 1.4x marker width.
6. Let users click a collapsed stack once to expand it horizontally with a highlight frame.
7. Add a small collapse button in the expanded stack so users can fold it again.
8. Keep individual event markers clickable after expansion.

## Verification

- Rebuild `exports/delivery/gantt.html`.
- Check generated JavaScript compiles.
- Browser-probe collapsed multi-event stack width does not exceed one date cell.
- Browser-probe collapsed stack click expands with highlighted frame and a collapse button.
- Browser-probe collapse button folds the stack again.
- Browser-probe marker click opens event detail after expansion.
- Browser-probe `Push changes` writes through the local server endpoint when available.
