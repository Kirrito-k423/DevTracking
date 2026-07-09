---
status: resolved
trigger: "User reports newly added verl专项 is missing again after previous autosave/portable backup fixes."
created: 2026-07-09
updated: 2026-07-09
---

# Debug Session: gantt-verl-loss

## Symptoms

- Expected behavior: a manually added `verl专项`/`VeRL-Omni专项` task remains visible after refresh/reopen.
- Actual behavior: user reports the task is not visible.
- Timeline: reported on 2026-07-09 after realtime autosave, portable backup, import/export, and desktop release changes.
- Reproduction: likely refresh/reopen `http://127.0.0.1:8091/gantt.html` after editing.

## Current Focus

- hypothesis: Browser localStorage can still override richer disk snapshots when its timestamp is newer, hiding tasks that are present in autosave/pushed/portable files.
- test: Compare disk snapshot contents and inspect restore selection logic.
- expecting: Disk files contain `VeRL-Omni专项`; restore code lets localStorage win by timestamp alone.
- next_action: fixed; regenerate and deploy Gantt page.

## Evidence

- timestamp: 2026-07-09T07:13:29Z
  finding: Current evidence snapshot copied to `.planning/recovery/gantt-verl-loss-20260709T071329Z`.
- timestamp: 2026-07-09T07:16:00Z
  finding: `exports/delivery/gantt-autosave.json`, `exports/delivery/gantt-local-edits.json`, and `portable/gantt/latest/gantt-local-edits.json` all contain 49 tasks / 46 events and include `VeRL-Omni专项`, `verl/veomni opd qwen35 35Bto2B 当前SMA26%`, and `verl 需求跟踪`.
- timestamp: 2026-07-09T07:16:00Z
  finding: `selectRestoreCandidate()` currently lets localStorage win over file candidates when localStorage has a newer timestamp, without checking whether it drops tasks/events that exist in file snapshots.
- timestamp: 2026-07-09T07:22:00Z
  finding: Added restore safety; localStorage no longer wins over autosave/pushed/portable if it would drop file snapshot tasks/events without matching tombstones.
- timestamp: 2026-07-09T07:22:00Z
  finding: Rebuilt `exports/delivery/gantt.html` and `portable/gantt/latest/gantt.html`; all three restore APIs return 49 tasks / 46 events and include `VeRL-Omni专项`.

## Eliminated

- hypothesis: Disk autosave and portable snapshots lost the `verl` tasks.
  reason: Current disk snapshots still contain the relevant `verl` tasks.

## Resolution

- root_cause: Browser localStorage restore was timestamp-based only. A newer but stale localStorage snapshot could hide tasks that were safely present in disk autosave/pushed/portable snapshots.
- fix: `selectRestoreCandidate()` now checks whether localStorage preserves file snapshot task/event IDs before letting it override autosave/pushed/portable candidates.
- verification: Python compile passed; generated Gantt JavaScript passes `node --check`; restore APIs for autosave, pushed changes, and portable all return 49 tasks / 46 events and contain `VeRL-Omni专项`; a Node simulation confirms stale localStorage selects autosave.
- files_changed: `scripts/build-delivery-dashboard.py`, `portable/gantt/latest/`
