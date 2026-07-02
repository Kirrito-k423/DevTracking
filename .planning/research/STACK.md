# Stack Research: Plane Demand Hub

## Recommendation

Use Plane as the project-management substrate and build a small sidecar service around it.

## Stack

| Layer | Choice | Rationale | Confidence |
|-------|--------|-----------|------------|
| Project/task UI | Plane Community Edition v1.3.1 | Already running locally; attractive work item, project, cycle, module, roadmap, and kanban UX | High |
| Plane deployment | Docker Compose | Official local self-hosting path; already verified at `http://localhost:8090` | High |
| Analytics source | Read-only PostgreSQL queries against Plane DB | Complete local access to work item, comments, and activity history | High |
| Write path | Plane API / webhooks / supported import paths | Avoids direct DB mutation risks | High |
| Sidecar backend | Python FastAPI | Good fit for AI, parsing, report generation, scheduled jobs, and local scripts | Medium |
| Sidecar DB | PostgreSQL, separate schema or separate DB | Keeps Demand Hub state separate from Plane internals | High |
| Jobs | Python scheduler first; Redis/RQ later if needed | Avoids new infrastructure until report jobs grow | Medium |
| Reports | Markdown/JSONL first, HTML/PDF/PPT later | Easy GitHub backup and AI consumption | High |
| Visualization | Plane views first; lightweight custom dashboard later | Avoids duplicating Plane UI before the workflow is proven | High |

## What Not To Do

- Do not fork Plane first. That makes upgrades harder and shifts effort away from the product's differentiator.
- Do not write directly into `issues`, `issue_comments`, or `issue_activities` for normal operations.
- Do not start with a large HR platform. Capability modeling should be scoped to delivery assignment, workload, blockers, and contribution visibility.

