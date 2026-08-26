---
status: ready
created: 2026-07-08
quick_id: 260708-duv
---

# Quick Task 260708-duv: Add Today Column Highlight and New Gantt Event Types

## Scope

- Highlight today's timeline column in light yellow across the header and all timeline rows.
- Add event types for `todo`, `阻塞`, and `重启` without removing the existing `求助`, `进行中`, `完成`, and `里程碑` types.
- Keep event creation/editing, marker rendering, summary counts, and generated HTML behavior consistent.

## Tasks

1. Update Gantt CSS and render logic for today's column highlighting.
2. Extend event type symbols, labels, ordering, marker colors, normalization, prompt text, and summary counts.
3. Regenerate the Gantt export and verify through browser smoke checks.

## Verification

- Python compile passes.
- Gantt export regenerates successfully.
- Generated inline JavaScript parses.
- Browser smoke test confirms today's header/rows are highlighted and new marker types normalize/render correctly.
