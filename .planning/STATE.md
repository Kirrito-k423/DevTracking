---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: MVP
status: Awaiting next milestone
last_updated: "2026-07-09T07:17:46Z"
last_activity: 2026-07-09 — Gantt stale localStorage restore bug fixed
progress:
  total_phases: 6
  completed_phases: 6
  total_plans: 6
  completed_plans: 6
  percent: 100
---

# State: Plane Demand Hub

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-07-06)

**Core value:** Turn natural-language team progress into trustworthy Plane state, visual timelines, and delivery reports without making every contributor do heavy manual bookkeeping.
**Current focus:** Milestone v1.0 MVP is archived; next recommended command is `$gsd-new-milestone`.

## Current Status

- Project initialized.
- Local Plane is running at `http://localhost:8090`.
- Phase 1 connector foundation is complete and verified.
- Plane health check, read-only timeline export, progress parser, and API comment writer dry-run all pass.
- Phase 1 local ship recorded; PR creation skipped because no git remote is configured.
- Phase 2 conversational progress preview has been executed.
- Seed update now resolves `SFT任务` to Plane issue `1-1 InternS2 SFT` and keeps unresolved `chunkmoe` as a draft/manual-target change.
- Phase 2 verification passed.
- Phase 2 local ship recorded; PR creation skipped because no git remote is configured.
- Phase 3 delivery dashboard has been executed.
- Dashboard outputs now include project `浦江`, issue `InternS2 SFT`, blocker `排队一天`, people evidence, and unresolved draft `chunkmoe`.
- Phase 3 verification passed.
- Phase 3 local ship recorded; PR creation skipped because no git remote is configured.
- Phase 4 reports, AI context, and backup manifest have been executed.
- Reports include daily, weekly, risk-help, retrospective, AI context JSONL, and a local backup manifest.
- Phase 4 verification passed.
- Phase 4 local ship recorded; PR creation skipped because no git remote is configured.
- Phase 5 demand triage and capability matching have been executed.
- Clear demand now produces ranked draft Plane changes and assignee recommendation; unclear demand is bounced back.
- Phase 5 verification passed.
- Phase 5 local ship recorded; PR creation skipped because no git remote is configured.
- Phase 6 Gantt sidecar has been executed and verified.
- Generated `exports/delivery/gantt.json` and `exports/delivery/gantt.html` from Plane timeline and progress audits.
- Phase 6 plan summary is ready at `.planning/phases/06-redesign-plane-gantt-visualization/06-01-SUMMARY.md`.
- Phase 6 verification passed at `.planning/phases/06-redesign-plane-gantt-visualization/06-VERIFICATION.md`.
- Phase 6 shipped via `codex/phase-06-gantt` PR #1: `https://github.com/Kirrito-k423/DevTracking/pull/1`.
- Gantt sidecar local interaction editing quick task completed: row drag hierarchy/order, bar resize, rename, event creation, and 30-day task-date padding.
- Gantt event marker refinement completed: long-press event creation works on bars and markers, same-day events render as opaque icon groups, and task table names use full titles.
- Gantt persistence and multi-event overlap completed: `Push changes` writes local auditable changesets, and collapsed same-day event stacks stay within one date cell before expansion.
- Gantt event stack visual polish completed: same-day event stack backgrounds, icons, collapse control, and expanded frame are vertically centered and visually balanced.
- Gantt detail drawer delete actions completed: task and event detail drawers include red delete buttons, and changesets record deleted tasks/events.
- Gantt visible add buttons completed: toolbar buttons now create task bars and events, and changesets record new task bars separately from task edits.
- Gantt editing polish completed: manual row order survives refresh, events can be edited, `进行中` arrow markers are supported, and task fields/colors are editable.
- Gantt row interaction polish completed: left-side rows can collapse/expand, task bar labels stay visible while scrolling the timeline, and Owner cells support double-click editing.
- Gantt report export and today centering completed: toolbar reports export daily/weekly/monthly Markdown by date range, and refresh centers today's date in the timeline.
- Gantt stale task bar fading completed: task bars begin fading after 6 days without a task event and clamp to 0.1 opacity for very stale tasks.
- Gantt fade thresholds and holiday headers completed: task bars keep original color for 0-1 day recent events, fade from day 2, clamp at 0.1 by day 6, and timeline headers mark weekends/holidays grey.
- Gantt stale fade inheritance bugfix completed: parent task fading now accounts for descendant events, and locally added task bars fade from their start date until an explicit event refreshes them.
- Gantt event add realtime stale color refresh completed: newly added events immediately refresh stale task bar colors via event source timestamps, and toolbar event dates default to today.
- Gantt today highlight and event types completed: today's timeline column is highlighted in light yellow, and event markers now support todo, grey 阻塞, and yellow 重启 while preserving red 求助.
- Gantt row drag hierarchy choices completed: row dragging now shows explicit horizontal indentation choices for same-level, child, and ancestor-level placements.
- Gantt manual task numbering completed: manually added task bars now receive local `N-x` keys instead of displaying `NEW`, with existing local `NEW` tasks migrated on load.
- Gantt portable snapshot export completed: `portable/gantt/latest/` now stores a committed clone-ready snapshot, the page can export it with one button, and Windows launch helpers can serve it after clone.
- Gantt pushed edits recovery completed: recovered the 2026-07-09 11:29 pushed changeset to 49 tasks / 46 events, restored portable snapshot, and fixed startup precedence so pushed edits beat older portable snapshots.
- Gantt realtime autosave backups completed: browser edits now write debounced disk backups to `exports/delivery/gantt-autosave.json` plus rolling history, restore ahead of pushed/portable snapshots, and show toolbar save status.
- Gantt daily portable GitHub backup scheduled: `scripts/backup-gantt-portable.py` exports the newest autosave/pushed state to `portable/gantt/latest/`, commits it, and a local Codex cron automation runs it daily at midnight.
- Gantt import/export usability and desktop release packaging completed: the toolbar now has separate migration `导出`/`导入` controls, zip drag/drop import, a desktop launcher, PyInstaller spec, and GitHub Release `gantt-app-v0.1.0` with Windows/macOS zip assets.
- Gantt stale localStorage restore bug fixed: disk snapshots still contained `VeRL-Omni专项`; restore now rejects newer localStorage when it would hide tasks/events present in autosave/pushed/portable snapshots.
- Milestone v1.0 MVP archived to `.planning/milestones/`.
- Next recommended command: `$gsd-new-milestone`

## Phase Status

| Phase | Status | Milestone Progress |
|-------|--------|--------------------|
| 1 | Complete | 17% |
| 2 | Complete | 33% |
| 3 | Complete | 50% |
| 4 | Complete | 67% |
| 5 | Complete | 83% |
| 6 | Complete | 100% |

## Active Decisions

- Use Plane as the visual source of truth.
- Build Demand Hub as a sidecar, not a Plane fork.
- Read Plane DB for analytics; write through API-level paths.
- Start with conversation-to-Plane daily progress loop.
- Improve visualization through a Demand Hub Gantt sidecar view rather than forking Plane.

## Accumulated Context

### Roadmap Evolution

- Phase 6 added: Redesign Plane Gantt Visualization — Gantt-first collapsible hierarchy, parent-child connector lines, clickable event markers, and 8-character default summaries.

## Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260709-kmq | Gantt import/export usability and desktop release packaging | 2026-07-09 | 6f5da4b | [260709-kmq-improve-gantt-import-export-usability-an](./quick/260709-kmq-improve-gantt-import-export-usability-an/) |
| 260709-k9p | Gantt daily portable GitHub backup | 2026-07-09 | bf9e3e0 | [260709-k9p-schedule-daily-midnight-backup-of-gantt-](./quick/260709-k9p-schedule-daily-midnight-backup-of-gantt-/) |
| 260709-jxg | Gantt realtime autosave backups | 2026-07-09 | fce58ce | [260709-jxg-add-realtime-gantt-autosave-backups](./quick/260709-jxg-add-realtime-gantt-autosave-backups/) |
| 260709-jss | Gantt pushed edits recovery and restore precedence fix | 2026-07-09 | 3cb9ccc | [260709-jss-recover-pushed-gantt-changes-and-fix-por](./quick/260709-jss-recover-pushed-gantt-changes-and-fix-por/) |
| 260708-ocv | Gantt portable snapshot export | 2026-07-08 | 9c98c2e | [260708-ocv-add-portable-gantt-snapshot-export](./quick/260708-ocv-add-portable-gantt-snapshot-export/) |
| 260708-grn | Gantt manual task numbering | 2026-07-08 | 867df19 | [260708-grn-fix-manual-gantt-task-numbering](./quick/260708-grn-fix-manual-gantt-task-numbering/) |
| 260708-f24 | Gantt row drag hierarchy drop choices | 2026-07-08 | 03f8ef5 | [260708-f24-improve-gantt-row-drag-hierarchy-drop-ch](./quick/260708-f24-improve-gantt-row-drag-hierarchy-drop-ch/) |
| 260708-duv | Gantt today column highlight and new event types | 2026-07-08 | 7fc316e | [260708-duv-add-today-column-highlight-and-new-gantt](./quick/260708-duv-add-today-column-highlight-and-new-gantt/) |
| 260708-dbz | Gantt event add realtime stale color refresh | 2026-07-08 | 49212f5 | [260708-dbz-fix-gantt-event-add-realtime-stale-color](./quick/260708-dbz-fix-gantt-event-add-realtime-stale-color/) |
| 260708-d1x | Gantt stale fade event inheritance and local task coverage | 2026-07-08 | 1bef8f8 | [260708-d1x-fix-gantt-stale-fade-event-inheritance-a](./quick/260708-d1x-fix-gantt-stale-fade-event-inheritance-a/) |
| 260707-tuf | Gantt fade thresholds and holiday headers | 2026-07-07 | 54e8cf1 | [260707-tuf-adjust-gantt-stale-fade-thresholds-and-g](./quick/260707-tuf-adjust-gantt-stale-fade-thresholds-and-g/) |
| 260707-tn0 | Gantt stale task bar fading | 2026-07-07 | 55e5e03 | [260707-tn0-fade-stale-gantt-task-bars-based-on-days](./quick/260707-tn0-fade-stale-gantt-task-bars-based-on-days/) |
| 260707-ono | Gantt report export and today centering | 2026-07-07 | e50c83a | [260707-ono-add-gantt-report-export-button-with-date](./quick/260707-ono-add-gantt-report-export-button-with-date/) |
| 260707-ogc | Gantt row interaction polish | 2026-07-07 | 22647f5 | [260707-ogc-polish-gantt-row-toggle-sticky-bar-label](./quick/260707-ogc-polish-gantt-row-toggle-sticky-bar-label/) |
| 260707-nlu | Gantt editing polish | 2026-07-07 | 8c72ddc | [260707-nlu-polish-gantt-persistence-editing-events-](./quick/260707-nlu-polish-gantt-persistence-editing-events-/) |
| 260707-kua | Gantt visible add buttons | 2026-07-07 | 8add2bf | [260707-kua-add-visible-gantt-add-buttons-for-new-ta](./quick/260707-kua-add-visible-gantt-add-buttons-for-new-ta/) |
| 260707-g32 | Gantt detail drawer delete actions | 2026-07-07 | 0cdc1ad | [260707-g32-gantt-detail-drawer-delete-actions-for-t](./quick/260707-g32-gantt-detail-drawer-delete-actions-for-t/) |
| 260707-frp | Gantt event stack visual polish | 2026-07-07 | 2f16280 | [260707-frp-polish-gantt-same-day-event-stack-visual](./quick/260707-frp-polish-gantt-same-day-event-stack-visual/) |
| 260707-fho | Gantt persistence and multi-event overlap | 2026-07-07 | 734cbd6 | [260707-fho-gantt-persistence-and-multi-event-overla](./quick/260707-fho-gantt-persistence-and-multi-event-overla/) |
| 260707-esq | Gantt event marker refinements | 2026-07-07 | b9054e4 | [260707-esq-gantt-event-creation-and-marker-visualiz](./quick/260707-esq-gantt-event-creation-and-marker-visualiz/) |
| 260707-ea2 | Gantt local interaction editing | 2026-07-07 | ba17415 | [260707-ea2-gantt-sidecar-local-interaction-editing-](./quick/260707-ea2-gantt-sidecar-local-interaction-editing-/) |
| 260707-dwc | Gantt readability fixes | 2026-07-07 | d3d8453 | [260707-dwc-gantt](./quick/260707-dwc-gantt/) |
| 260706-pdr | Plane daily record skill and July 6 daily update | 2026-07-06 | 501a728 | [260706-pdr-plane-daily-record](./quick/260706-pdr-plane-daily-record/) |
| 260706-q3p | Plane daily nested Q3 and ByteDance specials | 2026-07-06 | 9c184c6 | [260706-q3p-plane-daily-q3-specials](./quick/260706-q3p-plane-daily-q3-specials/) |

---
*State initialized: 2026-07-02*

## Performance Metrics

| Phase | Plan | Duration | Notes |
|-------|------|----------|-------|
| Phase 06 P01 | 9 min | 4 tasks | 5 files |

## Current Position

Phase: Milestone v1.0 complete
Plan: —
Status: Awaiting next milestone
Last activity: 2026-07-09 — Gantt stale localStorage restore bug fixed

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
