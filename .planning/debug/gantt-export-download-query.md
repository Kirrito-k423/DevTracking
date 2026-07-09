---
status: resolved
trigger: "Clicking Gantt 导出 opens /api/gantt-portable/download?t=... and returns 404 File not found."
created: 2026-07-09
updated: 2026-07-09
---

# Debug Session: gantt-export-download-query

## Symptoms

- Expected behavior: clicking `导出` downloads a portable Gantt zip package.
- Actual behavior: browser navigates to `/api/gantt-portable/download?t=...` and shows a 404 static file error page.

## Current Focus

- hypothesis: server API route matching uses `self.path` including the query string.
- test: compare `/api/gantt-portable/download` and `/api/gantt-portable/download?t=...`.
- expecting: no-query URL returns zip; query URL falls through to static file handler.
- next_action: fixed.

## Evidence

- timestamp: 2026-07-09T07:30:00Z
  finding: `/api/gantt-portable/download` returned `200 application/zip`; `/api/gantt-portable/download?t=1783582000134` returned `404 text/html`.
- timestamp: 2026-07-09T07:32:00Z
  finding: `DeliveryHandler.do_GET()` and `do_POST()` used `self.path.rstrip("/")`, so query strings prevented exact API route matching.

## Resolution

- root_cause: API route matching did not strip URL query strings.
- fix: Added `_route_path()` using `urllib.parse.urlsplit(self.path).path`, and used it for GET and POST routing.
- verification: `curl /api/gantt-portable/download?t=...` now returns `200 application/zip`; downloaded zip contains the expected portable files and a 52 task / 47 event `gantt-local-edits.json` including `VeRL专项`.
- files_changed: `scripts/serve-delivery-dashboard.py`, `portable/gantt/latest/`
