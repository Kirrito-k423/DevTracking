# Plane Demand Hub

## What This Is

Plane Demand Hub is a local-first delivery coordination system built around a self-hosted Plane instance. Plane remains the visual project, task, cycle, module, roadmap, and kanban surface; the custom layer turns conversational daily progress updates into structured Plane changes, timeline data, dashboards, reports, maintained delivery plans, demand triage, capability matching, and a Gantt sidecar view.

The first working mode is conversational: the user tells Codex each person's daily progress, blockers, risks, and next steps; Codex or a small local service parses that update, writes the right comments/status changes/work items into Plane through controlled API-level paths, then refreshes visual progress and reports.

## Core Value

Turn natural-language team progress into trustworthy Plane state, visual timelines, and delivery reports without making every contributor do heavy manual bookkeeping.

## Requirements

### Validated

- ✓ Plane local health, read-only timeline extraction, source references, and API-level write boundary — v1.0
- ✓ Natural-language daily progress parsing, conservative Plane target resolution, ambiguity handling, preview, and audit trail — v1.0
- ✓ Static delivery dashboard and Markdown delivery plan for project, person, blocker, stale-work, source, and timeline views — v1.0
- ✓ Daily, weekly, risk-help, retrospective, bounded AI context, and backup manifest generation — v1.0
- ✓ Demand intake, bounce-back, prioritization, draft Plane work-item creation, capability matrix, and assignee recommendation — v1.0
- ✓ Local static Gantt sidecar with Plane hierarchy, connector lines, blocker/completion/milestone markers, delivery-summary details, and dense/presentation modes — v1.0

### Active

Next milestone requirements are not selected yet. Candidate directions from the archived v2 backlog:

- [ ] Integrate Slack or chat channels for direct progress intake.
- [ ] Integrate GitHub commits, issues, and pull requests as extra progress signals.
- [ ] Generate Excel and PowerPoint versions of weekly and retrospective reports.
- [ ] Run scheduled report generation, send digests, and trigger blocker escalation workflows.
- [ ] Support multi-workspace Plane deployments.
- [ ] Harden live Plane API apply flows once the operator provides and scopes a Plane API key.

### Out of Scope

- Rebuilding Plane's project management UI - Plane already provides the attractive work item, project, roadmap, and kanban experience.
- Direct writes to Plane PostgreSQL for normal operations - this bypasses Plane business logic, activity logs, notifications, permissions, and sequence handling.
- Company-wide HR/payroll/performance management - v1 models delivery capability and workload only where it improves task assignment and reporting.
- Public SaaS multi-tenant deployment - v1 is local/self-hosted for one workspace.
- Full automatic truth inference from vague updates - ambiguous updates should ask for clarification or produce a draft before writing.

## Context

Current local state:

- Milestone v1.0 MVP shipped on 2026-07-06.
- Plane Community Edition v1.3.1 is running locally at `http://localhost:8090`.
- Deployment files live under `plane-selfhost/`.
- The local Plane PostgreSQL schema has been inspected. It includes key reporting tables such as `projects`, `issues`, `states`, `issue_assignees`, `issue_comments`, `issue_activities`, `cycles`, `modules`, and GitHub sync tables.
- A read-only timeline exporter exists at `scripts/export-plane-timeline.sh`; it writes JSONL timeline events under `exports/plane/`.
- The timeline exporter carries current Gantt issue fields such as `parent_id`, `start_date`, `target_date`, and `completed_at`.
- A static delivery dashboard is generated under `exports/delivery/`.
- A static Gantt sidecar is generated at `exports/delivery/gantt.html` with data at `exports/delivery/gantt.json`.
- Milestone archives live under `.planning/milestones/`.
- Phase 6 shipped through PR #1: `https://github.com/Kirrito-k423/DevTracking/pull/1`.

Existing docs:

- `LOCAL-PLANE-SOLUTION.md`
- `PLANE-DATA-INTEGRATION.md`
- `docs/PLANE-VISUAL-CONSTRUCTS.md`

Product framing from the user:

- Requirements should enter a filtering, bounce-back, and prioritization system before becoming work.
- Project progress, task assignment, and manpower/capability modeling should be connected.
- Individuals should be able to update their own progress, but the preferred near-term mode is conversational: the user reports daily progress and the assistant updates Plane.
- Outputs should include daily reports, weekly reports, risk-help summaries, project retrospective reports, high-density tables, and presentation-ready delivery views.
- Data should be recoverable and backed up to GitHub.

## Constraints

- **Local-first**: The system should run on the user's Mac and use the existing local Plane deployment first.
- **Network**: External network access may require proxy `127.0.0.1:7890`.
- **Data safety**: Plane database reads are allowed for reporting; writes should go through Plane API or a controlled connector.
- **Disk**: The Mac currently has limited free space after pulling Plane images; avoid unnecessary large services and image rebuilds.
- **Security**: Do not commit `plane.env`, API tokens, generated secrets, or direct personal contact/payment identifiers.
- **Maintainability**: Custom business data should live outside Plane's internal schema so Plane upgrades remain possible.
- **Interaction**: The working interface should support natural-language daily updates and produce confirmable structured changes.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Plane as the visual delivery source of truth | Plane already provides attractive, mature project/task/cycle/module/kanban UX | ✓ Validated in v1.0 |
| Build a custom Demand Hub sidecar instead of forking Plane | The differentiator is conversational progress capture, demand triage, reporting, capability matching, and improved delivery views | ✓ Validated in v1.0 |
| Read Plane PostgreSQL for analytics and AI context | Reporting needs complete historical data and timeline extraction | ✓ Validated in v1.0 |
| Write to Plane through API-level paths | Preserves Plane business logic, activity logs, permissions, notifications, and upgrade safety | ✓ Boundary implemented; live apply remains API-key gated |
| Start with conversation-to-Plane daily progress loop | This matches the user's preferred operating mode and creates immediate value | ✓ Validated in v1.0 |
| Keep custom business state separate from Plane schema | Reduces upgrade risk and makes GitHub backup/export cleaner | ✓ Validated in v1.0 |
| Improve Plane visualization through a Gantt sidecar | Plane remains the work system while Demand Hub adds collapsible hierarchy, connectors, event markers, and compact delivery summaries | ✓ Validated in Phase 6 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone**:
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-06 after v1.0 MVP milestone*
