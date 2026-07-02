## Local Operating Rules

- 始终用中文和用户对话。
- 这台位于中国的 macOS 机器访问 GitHub、Google 等外网时，优先使用代理 `127.0.0.1:7890`。
- Plane 本地访问地址是 `http://localhost:8090`。
- Plane PostgreSQL 只用于只读抽取、报表、时间线和 AI 上下文；常规写入必须走 Plane API、webhook 或受控连接器。
- 不要提交 `plane-selfhost/plane-app/plane.env`、API token、生成 secret、远程服务器密码或任何直接个人联系/支付标识。
- 当用户用自然语言提供每日进展时，先结构化成人员、项目、任务、完成、阻塞、风险、下一步，再生成可确认的 Plane 变更计划。

<!-- GSD:project-start source:PROJECT.md -->

## Project

**Plane Demand Hub**

Plane Demand Hub is a local-first delivery coordination system built around a self-hosted Plane instance. Plane remains the visual project, task, cycle, module, and kanban surface; the custom layer turns conversational daily progress updates into structured Plane changes, timeline data, dashboards, reports, and maintained delivery plans.

The first working mode is conversational: the user tells Codex each person's daily progress, blockers, risks, and next steps; Codex or a small local service parses that update, writes the right comments/status changes/work items into Plane, then refreshes visual progress and reports.

**Core Value:** Turn natural-language team progress into trustworthy Plane state, visual timelines, and delivery reports without making every contributor do heavy manual bookkeeping.

### Constraints

- **Local-first**: The system should run on the user's Mac and use the existing local Plane deployment first.
- **Network**: External network access may require proxy `127.0.0.1:7890`.
- **Data safety**: Plane database reads are allowed for reporting; writes should go through Plane API or a controlled connector.
- **Disk**: The Mac currently has limited free space after pulling Plane images; avoid unnecessary large services and image rebuilds.
- **Security**: Do not commit `plane.env`, API tokens, generated secrets, or direct personal contact/payment identifiers.
- **Maintainability**: Custom business data should live outside Plane's internal schema so Plane upgrades remain possible.
- **Interaction**: The working interface should support natural-language daily updates and produce confirmable structured changes.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommendation

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

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
