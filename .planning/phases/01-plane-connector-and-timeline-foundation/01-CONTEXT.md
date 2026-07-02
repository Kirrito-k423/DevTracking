# Phase 1: Plane Connector And Timeline Foundation - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes the integration foundation for Plane Demand Hub. It must prove that the local Plane instance is reachable, that Plane data can be extracted safely through read-only PostgreSQL queries, that normalized timeline events can be exported, and that future writes will use an API-level connector rather than direct database mutation.

This phase does not build the full conversational daily update workflow. It prepares the safe read/write foundation that Phase 2 will use to support conversational progress updates such as: "侯玉峰，浦江项目，开发chunkmoe；于家硕，浦江项目，SFT任务排队一天。"

</domain>

<decisions>
## Implementation Decisions

### Plane health and configuration
- **D-01:** Treat the local Plane instance at `http://localhost:8090` as the first integration target.
- **D-02:** Add a repeatable health/config command that verifies HTTP reachability, Docker Compose service status, and the configured Plane release when available.
- **D-03:** Health checks must not print secrets from `plane-selfhost/plane-app/plane.env`.

### Read-only Plane extraction
- **D-04:** Plane PostgreSQL is allowed only as a read source for reporting, timeline, AI context, and backup verification.
- **D-05:** The first canonical export format is JSONL with one event per line.
- **D-06:** Timeline events must include event time, event type, workspace/project IDs, project name, issue ID/key/title, actor when available, and a payload object.
- **D-07:** The extractor must support a `SINCE` filter so daily/weekly/report windows can be generated without reprocessing everything.
- **D-08:** The extractor should continue to read core Plane tables already inspected: `projects`, `issues`, `states`, `issue_assignees`, `issue_comments`, `issue_activities`, `cycles`, `cycle_issues`, `modules`, `module_issues`, `labels`, and `issue_labels`.

### Plane write boundary
- **D-09:** Normal writes to Plane must go through API-level behavior or a controlled connector, not direct SQL mutations.
- **D-10:** Phase 1 should provide the minimal connector boundary and documentation needed for Phase 2 to create comments, update work items, or create follow-up work from confirmed progress events.
- **D-11:** If API authentication cannot be completed non-interactively, Phase 1 may stop at a connector interface plus documented token setup, but must still keep read-only extraction fully working.

### Source traceability
- **D-12:** Every report claim or AI summary should be traceable to a source issue key, comment/activity event, or exported timeline row.
- **D-13:** Exported timeline rows should be stable enough to serve as AI context and backup artifacts.
- **D-14:** Do not expose raw secrets, Plane env values, tokens, or direct personal contact/payment identifiers in exported artifacts.

### Test data and real case strategy
- **D-15:** Use the user's concrete case as the first scenario for Phase 2 and as a compatibility target for Phase 1 data shapes: 侯玉峰 on 浦江项目 is developing `chunkmoe`; 于家硕 on 浦江项目 has an SFT task queued for one day.
- **D-16:** If Plane has no relevant project/work items yet, Phase 1 should document or provide a safe fixture/seed path that creates test data through the future write connector or an explicit manual setup path, not direct SQL.

### the agent's Discretion
- Choose exact script names, output filenames, Python package structure, and CLI flag names.
- Choose whether the first writer connector is a dry-run adapter, API client skeleton, or token-backed real API call, depending on what can be verified locally without leaking credentials.
- Choose the minimal test approach that proves the read-only extractor does not mutate Plane.

</decisions>

<specifics>
## Specific Ideas

- The operating mode after this foundation is conversational: the user reports daily progress to Codex, and Codex turns it into structured Plane updates and visual/report outputs.
- Plane remains the attractive front-end for projects, tasks, cycles, modules, and kanban views.
- The sidecar should preserve upgrade safety by keeping custom state outside Plane's internal schema.
- The first real scenario to keep in view is the 浦江项目 progress update involving 侯玉峰 and 于家硕.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and requirements
- `.planning/PROJECT.md` — Product boundary, core value, constraints, and key decisions.
- `.planning/REQUIREMENTS.md` — Phase 1 requirements `PLANE-01` through `PLANE-05`.
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria.
- `.planning/STATE.md` — Current phase and project memory.

### Existing local Plane work
- `LOCAL-PLANE-SOLUTION.md` — Local Plane deployment status, commands, ports, and operational notes.
- `PLANE-DATA-INTEGRATION.md` — Database read/write boundary and inspected schema notes.
- `scripts/export-plane-timeline.sh` — Existing read-only timeline exporter.
- `plane-selfhost/plane-app/docker-compose.yaml` — Plane service topology and container names.
- `AGENTS.md` — Local operating rules, including Chinese communication and Plane DB safety boundaries.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/export-plane-timeline.sh`: Existing read-only SQL timeline exporter; should be hardened rather than replaced blindly.
- `plane-selfhost/setup.sh`: Official Plane self-host control script; useful for start/stop/logs/backup commands.
- `plane-selfhost/plane-app/docker-compose.yaml`: Defines service names (`plane-db`, `api`, `proxy`, etc.) and compose invocation shape.

### Established Patterns
- Local scripts should be runnable from repository root and derive paths relative to the repo.
- Secrets are sourced from `plane.env` at runtime and must not be printed or committed.
- Generated timeline/report exports should go under ignored `exports/`.

### Integration Points
- Plane HTTP endpoint: `http://localhost:8090`.
- Plane PostgreSQL container: `plane-app-plane-db-1`, accessed through Docker Compose.
- Plane API container: `api`; user-facing access goes through the `proxy` service.
- Existing report/AI context artifact shape: JSONL timeline rows.

</code_context>

<deferred>
## Deferred Ideas

- Full conversational parser and update confirmation workflow — Phase 2.
- Delivery dashboard and person workload visualization — Phase 3.
- Daily/weekly/risk/retrospective report generation — Phase 4.
- Requirement filtering, bounce-back, priority ranking, and capability matching — Phase 5.

</deferred>

---

*Phase: 01-plane-connector-and-timeline-foundation*
*Context gathered: 2026-07-02*

