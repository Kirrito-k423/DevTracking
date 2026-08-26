## Local Operating Rules

- 始终用中文和用户对话。
- 这台位于中国的 macOS 机器访问 GitHub、Google 等外网时，优先使用代理 `127.0.0.1:7890`。
- Delivery Gantt 本地访问地址是 `http://localhost:8090/gantt.html`。
- 甘特图是独立本地应用，不依赖 Docker、外部项目管理系统或数据库。
- 不要提交 API token、生成 secret、远程服务器密码或任何直接个人联系/支付标识。
- 保留旧 schema/localStorage 标识以兼容已有快照；不要仅为改名破坏历史数据导入。

<!-- GSD:project-start source:PROJECT.md -->

## Project

**Delivery Gantt**

Delivery Gantt is a standalone, local-first editable Gantt application. A lightweight Python standard-library server provides the page, autosave, attachment, and migration APIs, while committed portable snapshots make the data easy to move between machines.

The primary working mode is direct editing in the browser. Tasks, events, hierarchy, colors, attachments, and reports are maintained in the Gantt itself and persisted to local snapshots.

**Core Value:** Keep delivery plans visually editable, locally durable, portable, and independent of heavyweight infrastructure.

### Constraints

- **Local-first**: The system runs on the user's Mac and listens on loopback by default.
- **Network**: External network access may require proxy `127.0.0.1:7890`.
- **Data safety**: Preserve `exports/delivery/` runtime state and `portable/gantt/latest/` migration snapshots during changes.
- **Disk**: Avoid unnecessary large services and build artifacts.
- **Security**: Do not commit API tokens, generated secrets, or direct personal contact/payment identifiers.
- **Maintainability**: Use Python standard-library components unless a new dependency materially improves the product.
- **Interaction**: Direct browser editing, autosave, attachments, and import/export must remain functional.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommendation

## Stack

| Layer | Choice | Rationale | Confidence |
|-------|--------|-----------|------------|
| Local server | Python `ThreadingHTTPServer` | No third-party runtime dependency; supports local API routes and static files | High |
| UI | Committed standalone HTML/CSS/JavaScript | Portable and directly usable on macOS/Windows/Linux | High |
| Mutable data | JSON autosaves and changesets under `exports/delivery/` | Auditable, local, and easy to recover | High |
| Portable data | `portable/gantt/latest/` | Clone-ready cross-machine snapshot | High |
| Desktop package | PyInstaller | Produces a single launcher around the local server | High |
| Backup | Git commits of portable snapshots | Simple history and remote recovery | High |

## What Not To Do

- Do not reintroduce Docker or a database for the local Gantt without an explicit requirement.
- Do not rename legacy schema/storage identifiers without a migration path.
- Do not overwrite newer autosaves with an older portable snapshot.

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
