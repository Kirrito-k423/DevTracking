# Delivery Gantt

## What This Is

Delivery Gantt is a standalone, local-first editable Gantt application. It runs on a lightweight Python standard-library HTTP server and persists browser edits, events, attachments, autosaves, and migration snapshots as local files.

The application no longer depends on Plane, Docker, PostgreSQL, or another task system. Historical v1.0 planning records remain archived for traceability, but the active product is the custom Gantt itself.

## Core Value

Keep delivery plans visually editable, locally durable, portable between machines, and independent of heavyweight infrastructure.

## Requirements

### Validated

- ✓ Editable task hierarchy, dates, owners, colors, progress, row ordering, and connectors — v1.0
- ✓ Events, blockers, milestones, stale-state visuals, and task-scoped reports — v1.0
- ✓ Autosave, pushed changesets, recovery precedence, import/export, and clear/reset flows — v1.0
- ✓ Task/event attachments and portable ZIP round-trip — v1.0
- ✓ macOS, Linux, Windows, and PyInstaller launch paths — v1.0
- ✓ Standalone local deployment at `http://127.0.0.1:8090/gantt.html` without Docker — 2026-07-21

### Active

- [ ] Continue improving the Gantt directly as user needs emerge.
- [ ] Keep portable backup and desktop packaging healthy.

### Out of Scope

- Plane hosting, database extraction, API writes, or Plane-specific progress workflows.
- Reintroducing Docker or a database without an explicit product need.
- Public multi-tenant SaaS hosting.

## Context

- Runtime state lives under `exports/delivery/` and is ignored by Git.
- Clone-ready snapshots live under `portable/gantt/latest/`.
- The local service is `scripts/serve-delivery-dashboard.py`.
- The desktop launcher is `scripts/gantt_app.py`.
- The old `plane-demand-hub.*` schema and localStorage identifiers remain only for backward compatibility with existing data.
- Milestone v1.0 and earlier Plane-era records remain under `.planning/` as historical evidence.

## Constraints

- **Local-first**: Listen on loopback by default.
- **Data safety**: Preserve newer autosaves and portable snapshots during changes.
- **Portability**: Keep source launchers usable with Python 3.9+ on macOS, Linux, and Windows.
- **Dependencies**: Prefer the Python standard library and committed static assets.
- **Security**: Do not commit secrets or direct personal contact/payment identifiers.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Make the custom Gantt the product | The user no longer needs the former project-management backend | Active |
| Remove Plane and its Docker resources | Frees local resources and eliminates an unused dependency | Completed 2026-07-21 |
| Keep legacy data identifiers | Existing browser state and portable snapshots must continue to import | Active |
| Use JSON files for mutable state | Simple, auditable, recoverable, and portable | Validated |

---
*Last updated: 2026-07-21 after standalone Gantt pivot*
