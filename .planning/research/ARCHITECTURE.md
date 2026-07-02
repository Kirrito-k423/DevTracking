# Architecture Research: Plane Demand Hub

## Component Boundaries

```text
User conversation
  -> Progress Parser
  -> Change Plan
  -> Plane Writer
  -> Plane

Plane PostgreSQL
  -> Timeline Extractor
  -> AI Context Store / JSONL
  -> Report Generator
  -> Dashboard / GitHub Backup
```

## Components

| Component | Responsibility |
|-----------|----------------|
| Plane | Source of truth for project/task/cycle/module/comment/activity state |
| Timeline Extractor | Read-only SQL extraction from Plane DB into normalized JSONL events |
| Progress Parser | Turns natural-language daily updates into structured people/project/task/blocker events |
| Change Planner | Decides which Plane objects need comments, status updates, new tasks, or follow-ups |
| Plane Writer | Writes to Plane through API-level operations |
| Delivery Plan Maintainer | Detects stale work, unowned blockers, missing next actions, and milestone drift |
| Report Generator | Creates daily, weekly, risk-help, and retrospective reports |
| Dashboard | Visualizes delivery status by project, person, risk, blocker, and timeline |
| Backup Job | Exports JSONL/Markdown reports to GitHub |

## Build Order

1. Harden read-only extraction from Plane and define event schema.
2. Implement minimum write path through Plane API.
3. Add conversational update parsing and confirmation.
4. Add reports and dashboard from the normalized timeline.
5. Add demand triage and capability matching after the progress loop is useful.

