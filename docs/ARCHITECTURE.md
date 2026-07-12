# Plane Demand Hub Architecture and Design

This document describes the architecture implemented in the current repository. It covers the lightweight Gantt runtime, the optional Plane integration, delivery-data generation, persistence and recovery, and release packaging.

## Architecture diagram

- Interactive diagram: [Plane Demand Hub architecture](architecture/plane-demand-hub-architecture.html)
- Reproducible Archify source: [plane-demand-hub.architecture.json](architecture/plane-demand-hub.architecture.json)

The diagram is generated with [Archify](https://github.com/tt-a1i/archify). The HTML is self-contained and provides dark/light themes plus PNG, JPEG, WebP, and SVG export from its toolbar.

## Design summary

Plane Demand Hub is a local-first sidecar around Plane rather than a Plane fork. Plane remains the authoritative project and work-item system when integration is enabled. The custom layer adds conversational progress intake, read-only analytics extraction, delivery artifacts, reports, and an editable portable Gantt.

The system deliberately supports three runtime modes:

| Mode | Required components | Docker required | Intended use |
|---|---|---:|---|
| Packaged Gantt desktop app | `PlaneDemandHubGantt` executable | No | Open, edit, autosave, import, export, and report from the portable Gantt |
| Source Gantt sidecar | Python and `scripts/serve-delivery-dashboard.py` | No | Develop or run the local HTTP server directly |
| Plane-integrated Demand Hub | Python, Docker Compose, Plane services, `plane.env` | Yes | Refresh from Plane, write confirmed comments, and maintain Plane-backed delivery artifacts |

Docker is therefore an optional integration dependency, not a dependency of the standalone Gantt application.

## Component model

| Component | Implementation | Responsibility |
|---|---|---|
| Plane Web / API | Optional self-hosted Plane deployment | Supported write boundary for comments and other controlled changes |
| Plane PostgreSQL | `plane-selfhost/plane-app/docker-compose.yaml` | Analytics source for projects, work items, activities, comments, cycles, modules, assignees, and labels |
| Timeline exporter | `scripts/export-plane-timeline.py` and `scripts/export-plane-timeline.sh` | Runs a read-only PostgreSQL transaction and writes normalized timeline JSONL |
| Progress pipeline | `scripts/progress-to-plane.py`, `scripts/progress_lib.py`, `scripts/plane-api-comment.py` | Parses progress text, resolves Plane targets, creates an audit, and optionally applies confirmed comments |
| Delivery builder | `scripts/build-delivery-dashboard.py` | Combines timeline rows and progress audits into dashboard, Gantt, HTML, JSON, and Markdown artifacts |
| Report generator | `scripts/generate-delivery-reports.py` | Produces daily, weekly, risk-help, retrospective, AI-context, and backup-manifest outputs |
| Gantt UI | Generated `gantt.html` | Renders hierarchy, dates, event markers, editing controls, reports, and migration actions |
| Local HTTP sidecar | `scripts/serve-delivery-dashboard.py` | Serves static delivery files and bounded JSON/ZIP persistence APIs |
| Runtime snapshot store | `exports/delivery/` or the desktop application data directory | Holds autosave history, latest autosave, explicitly pushed edits, and generated artifacts |
| Portable snapshot | `portable/gantt/latest/` | Clone-ready fallback containing the page, base data, full edit snapshot, manifest, and launchers |
| Desktop launcher | `scripts/gantt_app.py` and `packaging/plane-demand-hub-gantt.spec` | Seeds user data, binds the local server, opens the browser, and packages a standalone executable |
| GitHub automation | `scripts/backup-gantt-portable.py` and `.github/workflows/release-gantt-app.yml` | Backs up portable state and builds Windows/macOS release assets on version tags |

## Primary data flows

### Plane analytics to delivery artifacts

1. The timeline exporter executes SQL inside the `plane-db` container using `begin read only`.
2. PostgreSQL rows are normalized into `exports/plane/timeline.jsonl`.
3. The delivery builder reads the timeline plus JSON audits from `exports/progress/`.
4. It creates `dashboard.json`, `gantt.json`, the interactive HTML views, and Markdown delivery output under `exports/delivery/`.
5. The report generator reads `dashboard.json` and writes reports plus bounded AI context under `exports/reports/`.

This path is analytical: it does not mutate Plane PostgreSQL.

### Conversational progress to Plane

1. `progress-to-plane.py` accepts text from an argument or standard input.
2. `progress_lib.py` structures the update and resolves it against the current timeline.
3. The default mode is dry-run. Planned changes and unresolved targets are written to a progress audit without changing Plane.
4. `--apply` requires `PLANE_API_KEY` and only invokes `plane-api-comment.py` for changes marked `plane_api_comment` and `apply_ready`.
5. Ambiguous or unsupported changes remain skipped or require an explicit target.

The API gate preserves Plane business logic, permissions, activity history, and upgrade safety.

### Gantt editing and autosave

1. The page starts with generated Gantt data embedded in or served alongside `gantt.html`.
2. Initialization queries four candidates: browser `localStorage`, disk autosave, explicitly pushed edits, and the portable snapshot.
3. Disk candidates are ordered by timestamp, then source priority: autosave, pushed edits, portable snapshot.
4. A newer browser snapshot can win only if it does not silently drop tasks or events found in the best disk snapshot unless matching tombstones exist.
5. Each edit updates `localStorage` immediately and schedules a debounced POST to `/api/gantt-autosave` after 900 ms.
6. Explicit **Push changes** writes a timestamped changeset plus `gantt-local-edits.json`; it does not write directly to Plane.

The server retains at most 200 timestamped autosaves. JSON request bodies are capped at 5 MB.

### Portable migration and backup

The server exposes portable export, download, import, latest-snapshot, and manifest endpoints. ZIP imports are capped at 20 MB, accept only a fixed allowlist of snapshot files, flatten filenames, and require a changeset containing task and event arrays.

`export-gantt-portable.py` creates a commit-friendly snapshot. `backup-gantt-portable.py` selects the newest valid full snapshot from autosave, pushed edits, or the existing portable copy, then limits Git staging to the portable output directory before committing and pushing.

The portable snapshot supports three recovery paths:

- Clone the repository and start a platform launcher.
- Download/import a portable ZIP through the Gantt page.
- Run the packaged desktop app, which seeds its application-data directory from the bundled snapshot on first use.

### Desktop packaging and release

`gantt_app.py` uses platform-specific mutable data directories:

- Windows: `%APPDATA%\Plane Demand Hub Gantt`
- macOS: `~/Library/Application Support/Plane Demand Hub Gantt`
- Linux: `$XDG_DATA_HOME/Plane Demand Hub Gantt` or `~/.local/share/Plane Demand Hub Gantt`

It prefers port 8091 and falls back to an operating-system-assigned port if that port cannot be bound. The PyInstaller specification bundles the server, exporter, generated snapshot, platform launchers, and the hidden imports needed by dynamically loaded modules.

Pushing a `gantt-app-v*` tag triggers `.github/workflows/release-gantt-app.yml`, which builds Windows and macOS executables, packages ZIP assets, and publishes or updates the matching GitHub Release.

## Trust and write boundaries

| Boundary | Rule | Enforcement |
|---|---|---|
| Plane database | Read-only analytics only | Export SQL starts a read-only transaction; normal scripts do not directly mutate Plane tables |
| Plane API | Confirmed supported writes | `--apply` plus `PLANE_API_KEY`; only apply-ready comment changes are dispatched |
| Local sidecar | Local machine only by default | Server defaults to `127.0.0.1`; mutable state is stored in repository exports or the desktop data directory |
| Portable import | Treat ZIP content as untrusted | 20 MB cap, filename allowlist, basename check, JSON validation, required full snapshot |
| Gantt changes | Local changeset, not automatic Plane truth | API responses state that applying to Plane requires a controlled writer |
| GitHub backup | Commit only portable artifacts | Backup script scopes Git status, staging, diff, commit, and push to the configured portable directory |
| Secrets | Never portable or committed | `plane.env`, Plane API keys, generated secrets, and personal identifiers are excluded from generated backup manifests and repository policy |

## Data contracts

### Timeline JSONL

Each line represents an ordered event with time, event type, workspace/project/work-item identifiers, actor, source reference, and payload. Current work-item fields used by Gantt generation include parent, start date, target date, completion date, priority, and state.

### Gantt changeset

The edit contract uses schema `plane-demand-hub.gantt-edits.v1`. It carries granular change arrays, deletion tombstones, generation timestamps, and a full `snapshot` containing `tasks` and `events`. The full snapshot makes portable recovery independent of the original Plane instance.

### Portable manifest

The portable contract uses schema `plane-demand-hub.gantt-portable.v1`. Its manifest records export time, source timestamps, expected files, and task/event/change counts.

## Key design decisions

| Decision | Rationale | Trade-off |
|---|---|---|
| Keep Plane as the authoritative work system | Reuses mature task, project, roadmap, permission, and activity behavior | Full synchronization requires the optional Plane deployment |
| Build a sidecar instead of forking Plane | Keeps upgrades possible and focuses custom code on progress intake, reports, and visualization | Two user surfaces must be explained and maintained |
| Use files as the sidecar data plane | JSONL/JSON/Markdown are inspectable, portable, diffable, and AI-friendly | Concurrency is local/single-operator rather than multi-user transactional |
| Separate analytics reads from operational writes | Reduces corruption and audit risk | Some desired bulk updates need new controlled API writers |
| Make Gantt independently runnable | Users can use Release assets without Docker or Plane | Portable state can diverge from Plane until an explicit synchronization path runs |
| Persist both browser and disk state | Fast edits survive refresh while disk history supports recovery | Restore selection needs timestamps, priorities, and anti-data-loss checks |
| Commit a full portable snapshot | A clone can reproduce the working plan without the original database | Repository history grows with snapshot updates |

## Failure and degradation behavior

- If Plane or Docker is unavailable, the standalone/source Gantt still runs from generated or portable data; Plane refresh and apply operations are unavailable.
- If autosave APIs are unavailable, the browser continues to keep local edits in `localStorage`, but disk recovery is degraded.
- If port 8091 is occupied, the desktop launcher binds a free port and opens that URL.
- Invalid or oversized JSON/ZIP inputs receive an HTTP error and are not persisted.
- A stale browser snapshot cannot replace a richer disk snapshot merely because its timestamp is newer.
- Backup refuses to switch branches automatically and verifies the expected branch before committing/pushing.

## Extension points

- Add controlled Plane writers for state transitions, assignments, and work-item creation while preserving preview/confirmation.
- Add chat or Slack intake ahead of `progress_lib.py` without changing downstream audit and resolution contracts.
- Add GitHub activity as another normalized progress source feeding the delivery builder.
- Add Excel/PDF/PowerPoint renderers that consume `dashboard.json` rather than querying Plane directly.
- Move scheduled jobs to a queue only when local Python scheduling is no longer sufficient.
- Support multiple Plane workspaces by making workspace/project resolution explicit in timeline and audit inputs.

## Diagram regeneration and verification

The committed JSON IR is the source of the diagram. With Archify installed, run:

```text
node <archify-skill>/bin/archify.mjs validate architecture docs/architecture/plane-demand-hub.architecture.json --json
node <archify-skill>/bin/archify.mjs render architecture docs/architecture/plane-demand-hub.architecture.json docs/architecture/plane-demand-hub-architecture.html
node <archify-skill>/bin/archify.mjs check docs/architecture/plane-demand-hub-architecture.html
```

Update the IR rather than editing the generated HTML. Archify owns layout validation, semantic colors, theme behavior, and export tooling.
