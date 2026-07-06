# Plane Demand Hub

## What This Is

Plane Demand Hub is a local-first delivery coordination system built around a self-hosted Plane instance. Plane remains the visual project, task, cycle, module, and kanban surface; the custom layer turns conversational daily progress updates into structured Plane changes, timeline data, dashboards, reports, and maintained delivery plans.

The first working mode is conversational: the user tells Codex each person's daily progress, blockers, risks, and next steps; Codex or a small local service parses that update, writes the right comments/status changes/work items into Plane, then refreshes visual progress and reports.

## Core Value

Turn natural-language team progress into trustworthy Plane state, visual timelines, and delivery reports without making every contributor do heavy manual bookkeeping.

## Requirements

### Validated

- Phase 6 validated that Demand Hub can add a local static Gantt sidecar without forking Plane UI.
- The Gantt sidecar can render Plane task hierarchy, connector lines, blocker/completion/milestone markers, delivery-summary details, and dense/presentation modes from local exports.

### Active

- [ ] Self-hosted Plane is the source of truth for projects, work items, states, cycles, modules, comments, and activity history.
- [ ] The system can read Plane PostgreSQL safely for reporting and AI timeline context.
- [ ] The system writes changes back to Plane through API-level integrations, not direct database mutation.
- [ ] The user can describe daily progress in conversation and have it converted into structured updates.
- [ ] Daily progress updates can create comments, update status, surface blockers, and maintain follow-up tasks in Plane.
- [ ] The system can visualize delivery state by project, person, blocker, risk, and timeline.
- [ ] The system can generate daily reports, weekly reports, risk-help summaries, and project retrospectives.
- [ ] Reports and machine-readable timeline exports can be backed up to GitHub.
- [ ] Demand intake, filtering, bounce-back, priority ranking, and capability matching are supported as the expansion path after the progress loop is reliable.

### Out of Scope

- Rebuilding Plane's project management UI - Plane already provides the attractive work item, project, roadmap, and kanban experience.
- Direct writes to Plane PostgreSQL for normal operations - this bypasses Plane business logic, activity logs, notifications, permissions, and sequence handling.
- Company-wide HR/payroll/performance management - v1 models delivery capability and workload only where it improves task assignment and reporting.
- Public SaaS multi-tenant deployment - v1 is local/self-hosted for one workspace.
- Full automatic truth inference from vague updates - ambiguous updates should ask for clarification or produce a draft before writing.

## Context

Current local state:

- Plane Community Edition v1.3.1 is running locally at `http://localhost:8090`.
- Deployment files live under `plane-selfhost/`.
- The local Plane PostgreSQL schema has been inspected. It includes key reporting tables such as `projects`, `issues`, `states`, `issue_assignees`, `issue_comments`, `issue_activities`, `cycles`, `modules`, and GitHub sync tables.
- A read-only timeline exporter exists at `scripts/export-plane-timeline.sh`; it writes JSONL timeline events under `exports/plane/`.
- The timeline exporter now carries current Gantt issue fields such as `parent_id`, `start_date`, `target_date`, and `completed_at`.
- A static Gantt sidecar is generated at `exports/delivery/gantt.html` with data at `exports/delivery/gantt.json`.
- Existing docs:
  - `LOCAL-PLANE-SOLUTION.md`
  - `PLANE-DATA-INTEGRATION.md`

Product framing from the user:

- Requirements should enter a filtering, bounce-back, and prioritization system before becoming work.
- Project progress, task assignment, and manpower/capability modeling should be connected.
- Individuals should be able to update their own progress, but the preferred near-term mode is conversational: the user reports daily progress and the assistant updates Plane.
- Outputs should include daily reports, weekly reports, risk-help summaries, and project retrospective reports covering key nodes, blockers, breakthroughs, and contributors.
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
| Use Plane as the visual delivery source of truth | Plane already provides attractive, mature project/task/cycle/module/kanban UX | - Pending |
| Build a custom Demand Hub sidecar instead of forking Plane | The differentiator is conversational progress capture, demand triage, reporting, and capability matching, not rebuilding task UI | - Validated in Phase 6 for Gantt visualization |
| Read Plane PostgreSQL for analytics and AI context | Reporting needs complete historical data and timeline extraction | - Pending |
| Write to Plane through API-level paths | Preserves Plane business logic, activity logs, permissions, notifications, and upgrade safety | - Pending |
| Start with conversation-to-Plane daily progress loop | This matches the user's preferred operating mode and creates immediate value | - Pending |
| Keep custom business state separate from Plane schema | Reduces upgrade risk and makes GitHub backup/export cleaner | - Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-06 after Phase 6 verification*
