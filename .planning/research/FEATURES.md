# Feature Research: Plane Demand Hub

## Table Stakes

- Read Plane projects, work items, states, comments, activities, assignees, cycles, and modules.
- Export Plane history as a normalized timeline for AI and reports.
- Parse a daily conversational update into people, projects, completed work, blockers, risks, next actions, and required Plane changes.
- Ask for clarification before writing ambiguous changes.
- Write comments and status/task updates back to Plane through an API-level connector.
- Generate daily and weekly summaries from Plane history.
- Show project and person progress in a scannable dashboard.
- Back up structured timeline exports and reports to GitHub.

## Differentiators

- Conversational operator mode: the user gives a natural-language update and the system maintains Plane.
- Delivery-plan maintainer: the system detects stale tasks, unassigned blockers, missing next actions, and timeline drift.
- Risk-help summaries: blockers are converted into clear help requests with owner, target, and escalation context.
- Project retrospectives: key nodes, blockers, breakthroughs, and contributors are extracted from historical traces.
- Demand triage: incoming requirements can be filtered, bounced back, prioritized, and converted into Plane work.
- Capability matching: tasks can be suggested to people based on skills, load, history, and current risk.

## Anti-Features

- Full HR/payroll/performance reviews in v1.
- Replacing Plane's UX.
- Treating AI-generated summaries as authoritative without source links to Plane events.
- Silent writes to Plane when the user's update is ambiguous.

