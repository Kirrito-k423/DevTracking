# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-07-06
**Phases:** 6 | **Plans:** 6 | **Sessions:** multiple local GSD turns

### What Was Built

- Plane local health, read-only timeline export, source traceability, and API-level write boundary.
- Natural-language daily progress parsing with preview, ambiguity handling, audit artifacts, and auth-gated Plane apply.
- Static delivery dashboard, delivery plan, reports, AI context, backup manifest, demand triage, capability matching, and assignment recommendation.
- Static Gantt sidecar with collapsible hierarchy, connector lines, blocker/completion/milestone markers, delivery-summary detail drawer, and dense/presentation modes.

### What Worked

- Keeping Plane as the source of truth avoided a UI fork and kept the custom layer focused on delivery coordination.
- JSONL/JSON/Markdown artifacts made progress, reports, and verification easy to inspect locally.
- Conservative write gates prevented ambiguous natural-language updates from silently mutating Plane.
- The Gantt sidecar proved the system can add richer visualization while preserving existing dashboard outputs.

### What Was Inefficient

- Requirements status lagged behind verification evidence until milestone audit, which required a consistency backfill.
- Early phase ship records assumed no remote; Phase 6 later needed a real PR branch once `origin` was available.
- Phase 6 visual QA could not use Playwright because the local Node environment does not expose the module.

### Patterns Established

- Plane PostgreSQL is read-only for analytics; normal writes go through API-level paths.
- Generated operational artifacts live under ignored `exports/`; durable planning evidence lives under `.planning/`.
- Sidecar views should preserve existing outputs and add new files rather than replacing established artifacts.
- Requirement completion should be recorded in all three audit sources: REQUIREMENTS, VERIFICATION, and SUMMARY frontmatter.

### Key Lessons

1. Keep `requirements-completed` metadata in summaries from the start of each phase to avoid audit-time repair.
2. Treat PR shipping as a branch/remote concern separate from local phase verification.
3. For frontend-like artifacts, add a browser-capable visual QA dependency only when it is already present or explicitly worth the install cost.
4. Keep active roadmap files small after milestone close and move full history into `.planning/milestones/`.

### Cost Observations

- Runtime exceeded the threshold where execution cost tracking should be recorded.
- Detailed token and RMB evidence should live in `RMB-Cost.md`; this retrospective only records the process implication.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | multiple | 6 | Established local-first Plane sidecar workflow from progress intake to Gantt visualization |

### Cumulative Quality

| Milestone | Verification | Coverage | Zero-Dep Additions |
|-----------|--------------|----------|-------------------|
| v1.0 | 6/6 phases passed | 40/40 v1 requirements | Static local sidecar and report generators reuse existing Python/HTML paths |

### Top Lessons (Verified Across Milestones)

1. Local, inspectable artifacts make AI-assisted delivery safer because every generated claim can point to a source file.
2. Sidecar architecture lets the system improve Plane workflows without taking on Plane UI ownership.
