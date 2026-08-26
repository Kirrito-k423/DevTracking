---
quick_id: 260707-frp
slug: polish-gantt-same-day-event-stack-visual
status: complete
completed: 2026-07-07T03:25:00Z
---

# Quick Task Summary: Polish Gantt same-day event stack visuals

## Result

Same-day event stacks now have a centered, intentional visual treatment instead of looking like shrunken icons inside a misaligned frame.

## Changes

- Changed event stack vertical positioning to `top: 50%` with `translateY(-50%)`.
- Gave collapsed stacks an opaque white pill background with balanced border and shadow.
- Tightened expanded stack height, padding, border radius, and shadow.
- Centered the collapse button vertically without pushing the marker icons.
- Kept marker glyphs visually centered inside their colored circles.
- Increased the minimum collapsed stack height so the background reads as a designed container.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Inline JavaScript syntax check passed with Node `new Function`.
- Local HTTP check: `http://127.0.0.1:8091/gantt.html` returned `200`.
- Browser pixel probe passed: row height `30px`; collapsed stack center delta `0.5px`; collapsed marker center delta `0.5px`; expanded stack center delta `0.5px`; expanded marker center delta `0.5px`; collapse-button center delta `0.5px`.
- Visual screenshot written to `/tmp/gantt-event-stack-polished-scrolled.png`.

## Notes

Existing ignored changeset files under `exports/delivery/` were left untouched.
