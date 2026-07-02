# Walking Skeleton: Plane Demand Hub

**Phase:** 1
**Generated:** 2026-07-02

## Capability Proven End-to-End

The operator can verify local Plane health, export a read-only source-backed timeline, parse a daily progress sentence into structured events, and produce a confirmable Plane change preview without directly mutating Plane tables.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Primary UI | Plane CE at `http://localhost:8090` | Reuses Plane's project, issue, kanban, cycle, module, and member UX |
| Sidecar shape | Local scripts first, Python service later | Fastest route to a reliable local workflow without adding infrastructure |
| Analytics source | Read-only Plane PostgreSQL queries | Complete local history for reports, timelines, and AI context |
| Write boundary | Dry-run/API connector interface | Preserves Plane business logic and avoids direct DB mutation |
| Artifact format | JSONL under ignored `exports/` | Easy for AI context, reports, backup, and source traceability |
| Deployment target | User's Mac with Docker Compose Plane | Matches current environment and avoids premature server work |

## Stack Touched in Phase 1

- [x] Project scaffold: GSD project and phase artifacts
- [x] Routing: CLI commands from repository root
- [x] Database read: read-only Plane PostgreSQL timeline export
- [ ] Database write: no direct Plane DB writes; dry-run change set proves future write boundary
- [x] UI surface: Plane remains reachable as the visual surface
- [x] Deployment: local Plane Docker Compose deployment at `http://localhost:8090`

## Out of Scope

- Full conversational clarification loop
- Real authenticated Plane API mutation without user-provided credentials
- Custom dashboard UI
- Scheduled report automation
- Demand prioritization and capability matching

## Subsequent Slice Plan

- Phase 2: Parse natural-language daily updates, preview changes, request confirmation, and apply confirmed changes through the Plane connector.
- Phase 3: Maintain delivery plans and visualize progress/person/blocker/timeline views.
- Phase 4: Generate daily, weekly, risk-help, and retrospective reports with backup.
- Phase 5: Add requirement triage, prioritization, and capability matching.

