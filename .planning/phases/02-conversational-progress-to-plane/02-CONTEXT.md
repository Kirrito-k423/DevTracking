# Phase 2: Conversational Progress To Plane - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning
**Mode:** auto

<domain>
## Phase Boundary

Phase 2 turns the user's natural-language daily progress messages into structured, confirmable Plane updates. It builds the first practical loop for the desired working mode: the user tells Codex who did what today, Codex parses the update, resolves likely Plane project/work-item targets, previews exactly what would change, and only applies changes through Plane API-level behavior when explicitly confirmed and authenticated.

This phase does not build the full dashboard, delivery visualization, report generator, or demand-prioritization system. Those stay in later phases.

</domain>

<decisions>
## Implementation Decisions

### Interaction contract
- **D-01:** The primary operator interface for this phase is a root-runnable CLI/script that Codex can call after the user provides a daily progress sentence.
- **D-02:** The first input shape is semicolon-separated or newline-separated Chinese progress updates, for example: `侯玉峰，浦江项目，开发chunkmoe；于家硕，浦江项目，SFT任务排队一天。`
- **D-03:** The output must always include the original message, parsed progress events, a human-readable preview, and machine-readable planned Plane changes.
- **D-04:** The system must support multi-person, same-project updates in one message.

### Safety and confirmation
- **D-05:** Default mode is preview/dry-run. No Plane mutation happens unless the operator uses an explicit confirmation/apply flag.
- **D-06:** Ambiguous person/project/work-item references must be flagged instead of silently writing.
- **D-07:** If `PLANE_API_KEY` is missing, the workflow should stop at an auth gate with exact next steps, not fall back to direct SQL.
- **D-08:** The system must never write directly to Plane PostgreSQL.

### Resolution behavior
- **D-09:** Project resolution should use Plane-derived project names plus aliases such as removing the suffix `项目`.
- **D-10:** Work-item resolution should prefer exact issue key, then exact/substring title, then conservative token matching for cases such as `SFT任务` matching an existing `InternS2 SFT` item.
- **D-11:** If one clear issue target exists, planned changes may point to that issue ID and API route.
- **D-12:** If no clear issue target exists, planned changes should remain as project-level notes or proposed follow-up work items for manual/API creation later.
- **D-13:** If multiple issue targets match, mark the change ambiguous and require clarification.

### Write behavior
- **D-14:** The first real write path is Plane work-item comment create/update through `scripts/plane-api-comment.py`.
- **D-15:** Blocker/waiting context should be represented as a comment first; status transitions or new follow-up tasks can be planned in the change set but should not be applied until exact target and intended action are clear.
- **D-16:** All applied changes must include an `external_id` derived from the source message/segment for traceability and idempotency.

### Audit trail
- **D-17:** Each run should write a local JSON artifact containing original input, parsed events, resolution results, planned changes, applied changes, skipped changes, warnings, and timestamp.
- **D-18:** Run artifacts should go under ignored local output (`exports/progress/`) for now; GitHub backup/export policy belongs to Phase 4.
- **D-19:** Every generated preview or apply result must preserve source references back to message ID and segment index.

### User case target
- **D-20:** The specific case `侯玉峰，浦江项目，开发chunkmoe；于家硕，浦江项目，SFT任务排队一天。` is the acceptance seed.
- **D-21:** For the current local Plane data, `浦江项目` should resolve to the existing Plane project alias `浦江`.
- **D-22:** `SFT任务` should be able to resolve to the existing `InternS2 SFT` work item via token matching.
- **D-23:** `chunkmoe` may remain unresolved if no matching Plane work item exists; the preview should explain that it needs a new work item or manual target selection.

### the agent's Discretion
- Choose exact script names, JSON field names, and output directory under `exports/`.
- Choose whether to extend existing parser scripts or add an orchestration script.
- Choose lightweight matching heuristics that are safe and testable without adding a heavy search service.
- Choose minimal terminal preview format; custom web visualization is deferred.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and Phase Scope
- `.planning/PROJECT.md` — Defines the conversational Plane sidecar goal and constraints.
- `.planning/REQUIREMENTS.md` — Defines `CONV-01` through `CONV-05`.
- `.planning/ROADMAP.md` — Defines Phase 2 goal and success criteria.
- `.planning/STATE.md` — Records Phase 1 completion and current focus.

### Phase 1 Foundation
- `.planning/phases/01-plane-connector-and-timeline-foundation/01-01-SUMMARY.md` — Lists implemented scripts and verification evidence.
- `.planning/phases/01-plane-connector-and-timeline-foundation/01-VERIFICATION.md` — Confirms Phase 1 connector foundation passed.
- `PLANE-DATA-INTEGRATION.md` — Documents DB read/API write boundary and Plane comment API route.

### Existing Scripts
- `scripts/parse-progress-case.py` — Existing parser for the user case; should be extended or reused.
- `scripts/plane-api-comment.py` — Plane API comment writer, dry-run by default.
- `scripts/export-plane-timeline.sh` — Read-only Plane timeline exporter with source fields and workspace slug.
- `scripts/plane-health.sh` — Plane health check.

### Local Plane Deployment
- `LOCAL-PLANE-SOLUTION.md` — Local Plane deployment status and operational commands.
- `plane-selfhost/plane-app/docker-compose.yaml` — Plane service topology.
- `AGENTS.md` — Local rules: Chinese communication, proxy, no secrets, no direct Plane DB writes.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/parse-progress-case.py`: Already parses the seed update into two events and three planned changes.
- `scripts/export-plane-timeline.sh`: Provides Plane project/work-item/timeline data and includes `workspace_slug`, `project_id`, `issue_id`, and source fields.
- `scripts/plane-api-comment.py`: Can create/update Plane comments through API when `PLANE_API_KEY` and `--apply` are provided.

### Established Patterns
- Scripts derive paths from repository root.
- Secrets are loaded from env or ignored files but never printed.
- Generated artifacts belong under ignored `exports/`.
- Plane DB reads are allowed; Plane DB writes are not.

### Integration Points
- Input: user natural-language progress message.
- Read source: `exports/plane/timeline.jsonl` generated from Plane DB.
- Write target: Plane API comment route.
- Audit output: local JSON under `exports/progress/`.

</code_context>

<specifics>
## Specific Ideas

- The system should feel like a conversation with Codex: the user says the update, Codex shows what it understood and what it intends to write.
- A preview should be concise enough to read quickly, but structured enough to audit.
- The first accepted behavior is not “fully autonomous writes”; it is “safe confirmed writes with evidence.”

</specifics>

<deferred>
## Deferred Ideas

- Web dashboard and timeline visualization: Phase 3.
- Daily/weekly/risk/retro report generation: Phase 4.
- GitHub backup of progress artifacts: Phase 4.
- Requirement triage and capability matching: Phase 5.
- Slack/chat ingestion: v2 integration.

</deferred>

---

*Phase: 02-Conversational Progress To Plane*
*Context gathered: 2026-07-02*

