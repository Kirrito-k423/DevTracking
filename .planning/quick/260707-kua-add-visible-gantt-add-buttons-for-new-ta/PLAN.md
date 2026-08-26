---
status: in_progress
quick_id: 260707-kua
date: 2026-07-07
---

# Add Visible Gantt Add Buttons

## Scope

- Add explicit toolbar buttons for creating a new task bar and creating a new event.
- Persist locally created task bars across reloads.
- Include locally created task bars and events in the auditable `Push changes` changeset.
- Keep Plane write safety unchanged: no direct Plane DB writes from the browser.

## Verification

- Rebuild `exports/delivery/gantt.html`.
- Run Python syntax checks for the dashboard scripts.
- Run a browser-level smoke test that creates a task and event through the new buttons.
