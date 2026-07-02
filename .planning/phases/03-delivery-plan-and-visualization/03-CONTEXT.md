# Phase 3: Delivery Plan And Visualization - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning
**Mode:** auto

<domain>
## Phase Boundary

Phase 3 turns Plane timeline data and conversational progress audit artifacts into a local delivery plan and a visual dashboard. It should let the operator inspect projects, owners, blockers, stale work, recent activity, and timeline evidence without manually assembling spreadsheets.

This phase does not generate daily/weekly reports, PowerPoint/Excel, GitHub backup, or requirement triage. Those stay in later phases.

</domain>

<decisions>
## Implementation Decisions

### Visualization surface
- **D-01:** Build a static local dashboard first, generated under ignored `exports/delivery/`.
- **D-02:** Do not start a new web service in this phase; the HTML should open directly in a browser.
- **D-03:** The dashboard should be operational and scan-friendly: compact cards, tables, simple bars/timelines, no marketing hero.

### Data sources
- **D-04:** Primary sources are `exports/plane/timeline.jsonl` and `exports/progress/*.json`.
- **D-05:** If source files are missing, the generator should explain what command to run rather than failing unclearly.
- **D-06:** Each displayed item should retain source references: Plane issue key/source table or progress source ID/segment.

### Delivery plan
- **D-07:** Generate a Markdown delivery plan beside the dashboard, grouped by project.
- **D-08:** For each project, show active tasks, likely owners from progress events, blockers/waiting items, unresolved drafts, recent activity, stale signals, and next review date.
- **D-09:** Use conservative inference; if owner/milestone is unknown, mark it unknown instead of inventing.

### Risk and blocker logic
- **D-10:** Waiting/blocker events from progress audits are blocker evidence.
- **D-11:** Unresolved progress changes are delivery risks because they indicate work not yet attached to a Plane item.
- **D-12:** Stale work detection should use a configurable age threshold, defaulting to 7 days.

### the agent's Discretion
- Choose exact HTML layout and CSS.
- Choose compact chart/table representations that work without external assets.
- Choose JSON schema for dashboard data.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and Requirements
- `.planning/PROJECT.md` — Defines the desired Plane-centered operating mode.
- `.planning/REQUIREMENTS.md` — Defines `DELV-01..DELV-05` and `VIS-01..VIS-04`.
- `.planning/ROADMAP.md` — Defines Phase 3 goal and success criteria.
- `.planning/STATE.md` — Current project status.

### Prior Phase Outputs
- `.planning/phases/01-plane-connector-and-timeline-foundation/01-VERIFICATION.md` — Confirms timeline export foundation.
- `.planning/phases/02-conversational-progress-to-plane/02-VERIFICATION.md` — Confirms conversational progress audit foundation.
- `.planning/phases/02-conversational-progress-to-plane/02-01-SUMMARY.md` — Describes progress audit shape and seed case behavior.

### Existing Scripts
- `scripts/export-plane-timeline.sh` — Produces Plane timeline source JSONL.
- `scripts/progress-to-plane.py` — Produces progress audit JSON under `exports/progress/`.
- `scripts/progress_lib.py` — Shared parsing/resolution helpers.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Timeline JSONL rows already include `workspace_slug`, `project_id`, `project`, `issue_id`, `issue_key`, `issue_title`, `source`, and `payload`.
- Progress audit JSON contains original input, events, planned changes, warnings, and resolution data.

### Established Patterns
- Scripts are root-runnable and use only Python stdlib.
- Generated files should go under ignored `exports/`.
- No secrets should be printed or written.

### Integration Points
- Input: `exports/plane/timeline.jsonl`, `exports/progress/*.json`.
- Output: `exports/delivery/dashboard.html`, `exports/delivery/dashboard.json`, `exports/delivery/delivery-plan.md`.

</code_context>

<specifics>
## Specific Ideas

- The dashboard should immediately show whether the user's seed case is visible: 于家硕/SFT waiting should appear as a blocker/waiting signal; chunkmoe should appear as an unresolved draft/risk.
- The Markdown delivery plan is the maintained delivery artifact for now.

</specifics>

<deferred>
## Deferred Ideas

- Scheduled report generation and GitHub backup: Phase 4.
- Custom interactive web app/server: later only if static dashboard is insufficient.
- Requirement triage/capability matrix: Phase 5.

</deferred>

---

*Phase: 03-Delivery Plan And Visualization*
*Context gathered: 2026-07-02*

