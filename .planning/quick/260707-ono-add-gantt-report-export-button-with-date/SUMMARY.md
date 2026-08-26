---
status: complete
quick_id: 260707-ono
date: 2026-07-07
---

# Summary

Added report export and today-centered timeline loading to the Gantt sidecar.

## Delivered

- Added an `输出报告` toolbar button.
- Added report type selection for 日报、周报、月报.
- Added date range prompts with sensible defaults for day, week, and month.
- Exported Markdown reports containing:
  - 进展
  - 下一步
  - 阻塞
  - 求助点
  - 事件明细
- Reports are generated from current Gantt page state, including local edits.
- Centered today's date after initial load/refresh.
- Made centering work across both desktop timeline scrolling and narrow-layout outer scrolling.

## Verification

- `python3 -m py_compile scripts/build-delivery-dashboard.py scripts/serve-delivery-dashboard.py`
- `python3 scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery`
- Node syntax check of generated `exports/delivery/gantt.html`
- Headless Chrome CDP smoke test:
  - `输出报告` exists
  - 月报 export produces Markdown with all required sections
  - today-centering scrolls the real horizontal scroller to the expected position
