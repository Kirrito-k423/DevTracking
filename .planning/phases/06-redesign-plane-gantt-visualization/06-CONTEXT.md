# Phase 6: Redesign Plane Gantt Visualization - Context

**Gathered:** 2026-07-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 builds a new Demand Hub Gantt visualization sidecar because Plane's current visualization is not usable enough for the operator's delivery-reading workflow. It should make the existing Plane task hierarchy, parent-child links, blockers, completions, milestones, and compact task/event summaries directly inspectable from local artifacts.

This phase does not fork Plane or replace Plane as the source of truth. Plane remains the task system; the new view reads Plane/Demand Hub exports and generates local visualization artifacts.

</domain>

<decisions>
## Implementation Decisions

### Visualization Surface
- **D-01:** Build a new Gantt view rather than trying to keep tuning the existing local dashboard as the main visualization.
- **D-02:** Preserve the existing dashboard artifacts; the new view should be a separate sidecar output, expected as `exports/delivery/gantt.html` plus supporting structured data.
- **D-03:** The view should remain local-first and static-file friendly unless research proves that a tiny local server is required for the interaction model.

### Task Hierarchy
- **D-04:** Use Plane `parent_id` as the authoritative hierarchy source for multi-level tasks.
- **D-05:** The Gantt task model must preserve task IDs, parent IDs, depth, sibling order, date range, status/progress, owner/labels/modules, and source references.
- **D-06:** Parent task bars should be clickable expand/collapse controls for their child tasks. Collapsed parents should keep a rolled-up bar that still conveys timing and progress.
- **D-07:** Parent-child connector lines are required and must remain readable when rows are collapsed, expanded, or horizontally scrolled.

### Event Semantics
- **D-08:** Event markers for blockers, completions, and milestones should come from Plane-native evidence first: labels, state, and `completed_at`.
- **D-09:** Marker mapping is locked as: blocker = red circled cross, completion = green dot, milestone = yellow star.
- **D-10:** Progress audit events can enrich detail text and source evidence, but they must not override Plane labels/state/completion as the primary marker semantics.

### Details And Summaries
- **D-11:** Clicking a task bar or event marker should open delivery-summary details by default, not a raw audit/debug panel.
- **D-12:** Detail content should prioritize what the operator needs to decide next: task title/key, owner if known, state/progress, date range, blocker or milestone summary, next action, and source links.
- **D-13:** Raw source evidence should still be available inside the details view, but secondary to the delivery summary.
- **D-14:** Task bars and event markers should show compact default summaries capped at 8 characters. Full text should be reachable through click or hover detail.

### Density Modes
- **D-15:** Support both high-density table mode and presentation/reporting mode.
- **D-16:** Default mode should be high-density for daily operational scanning.
- **D-17:** Presentation mode should be a toggle or alternate render state with larger rows, clearer labels, and less visual clutter while preserving the same task/event data.

### the agent's Discretion
- Choose exact HTML/CSS/JavaScript implementation details, provided the output stays local-first and does not introduce unnecessary infrastructure.
- Choose whether to extend `scripts/build-delivery-dashboard.py` or create a focused new script, as long as the existing dashboard is not broken.
- Choose the exact connector-line drawing method after researching what works best for static HTML.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Requirements
- `.planning/PROJECT.md` — Defines Plane as the source of truth and Demand Hub as the sidecar layer.
- `.planning/ROADMAP.md` — Defines Phase 6 goal, dependencies, and success criteria.
- `.planning/REQUIREMENTS.md` — Defines `GANTT-01..GANTT-06`.
- `.planning/STATE.md` — Records the Phase 6 extension and prior shipped phases.

### Prior Visualization And Data Sources
- `.planning/phases/03-delivery-plan-and-visualization/03-CONTEXT.md` — Prior dashboard decisions: static local HTML, `exports/`, source references, operational density.
- `.planning/phases/03-delivery-plan-and-visualization/03-01-SUMMARY.md` — Confirms current dashboard artifacts and residual risks.
- `scripts/build-delivery-dashboard.py` — Existing static dashboard generator and JSON/HTML/Markdown output pattern.
- `exports/delivery/dashboard.json` — Current consolidated project/person/blocker/timeline data.
- `exports/plane/timeline.jsonl` — Plane timeline events and source references.
- `exports/progress/*.json` — Progress audit events that can enrich details.

### Plane Visual Constructs
- `docs/PLANE-VISUAL-CONSTRUCTS.md` — Existing Plane labels, views, modules, task relationships, and known gaps that motivated the redesign.
- `scripts/bootstrap-plane-visual-constructs.py` — Existing Plane-native Gantt view setup and label/module conventions.
- `scripts/apply-plane-daily-record.py` — Existing parent/date/label/module write model; exposes `parent_id`, date, state, labels, and modules in audit output.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/build-delivery-dashboard.py`: root-runnable Python stdlib script that loads timeline JSONL and progress audit JSON, writes `dashboard.json`, `dashboard.html`, and `delivery-plan.md`.
- `exports/delivery/dashboard.json`: already aggregates projects, issues, people, blockers, unresolved drafts, stale work, and recent timeline activity.
- `exports/plane/timeline.jsonl`: includes issue keys/titles, event types, source tables/IDs, state, priority, start/target date changes, completion events, label events, module events, and parent activity events.
- `exports/progress/*.json`: includes user progress events, blockers, labels, modules, and source IDs suitable for detail enrichment.
- `docs/PLANE-VISUAL-CONSTRUCTS.md`: documents real Plane views and task hierarchy such as `InternS2 SFT` -> `chunkmoe 性能优化` -> daily event tasks.

### Established Patterns
- Scripts are Python stdlib, root-runnable, and avoid new services unless needed.
- Generated artifacts live under ignored `exports/`.
- Visual outputs are static HTML/CSS/JS that can open directly in a browser.
- No secrets should be printed or committed.
- Plane database reads are allowed for reporting/extraction; normal writes stay API-level or controlled-script gated.

### Integration Points
- Input: `exports/plane/timeline.jsonl`, `exports/progress/*.json`, and optionally `exports/delivery/dashboard.json`.
- Output: new Gantt artifacts under `exports/delivery/`, expected `gantt.html` and a structured Gantt JSON file.
- Documentation: update `PLANE-DATA-INTEGRATION.md` and/or `docs/PLANE-VISUAL-CONSTRUCTS.md` with the new command and output paths.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly called the current Plane visualization "完全不能用" and wants improvement based on a Gantt chart.
- Multi-level tasks must be collapsible.
- Parent and child task bars must have visible connector lines.
- Clicking a parent task bar should expand or collapse child tasks.
- Event markers are required on task bars: blocked = red circled cross, completed = green dot, milestone = yellow star.
- Clicking an event marker should expand detailed information.
- Task bars and event markers should default to at most 8 characters of summary text.
- Both dense daily scanning and presentation/reporting views should be available.

</specifics>

<deferred>
## Deferred Ideas

- Rebuilding or forking the Plane application UI.
- Editing Plane internals to change its native Gantt behavior.
- Adding a large frontend framework or persistent web service unless research shows static HTML cannot satisfy the interaction requirements.

</deferred>

---

*Phase: 06-Redesign Plane Gantt Visualization*
*Context gathered: 2026-07-06*
