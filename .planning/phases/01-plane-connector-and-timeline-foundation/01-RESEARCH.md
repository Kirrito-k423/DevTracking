# Phase 1 Research: Plane Connector And Timeline Foundation

**Phase:** 01
**Date:** 2026-07-02
**Status:** Complete

## Research Question

How should the local Plane deployment be connected to a sidecar workflow that can read history for reports and prepare safe writes for conversational progress updates?

## Findings

### Local Plane shape

- Plane CE is already running locally at `http://localhost:8090`.
- The Docker Compose deployment keeps PostgreSQL inside the Plane Docker network.
- The repo already has `scripts/export-plane-timeline.sh`, which proves read access through `docker compose exec plane-db`.
- `plane-selfhost/plane-app/plane.env` contains database credentials and must stay uncommitted.

### Read strategy

The practical read path is a local script that:

1. Loads Plane DB credentials from the ignored env file.
2. Executes SQL inside the Plane DB container.
3. Runs inside a read-only transaction.
4. Emits normalized JSONL under `exports/`.

The first stable event schema should preserve:

- `event_time`
- `event_type`
- `workspace_id`
- `project_id`
- `project`
- `issue_id`
- `issue_key`
- `issue_title`
- `actor`
- `source`
- `payload`

The exporter should include issue creation/completion, comments, activities, assignees, cycles, modules, and labels where available. This is enough for daily reports, weekly reports, retrospectives, AI context windows, and traceable dashboard facts.

### Write strategy

Plane database writes are unsafe for normal operations because they can bypass business rules, activities, cache, notifications, permissions, issue sequencing, and future schema changes.

Phase 1 should therefore define a connector boundary rather than direct DB mutation:

- `dry-run`: parse progress text and emit a planned Plane change set.
- `api`: later use a Plane API token/session to create comments, update work items, and create follow-up tasks.
- `manual`: when auth is not configured, present the change set so the operator can apply it in Plane.

This keeps Phase 1 useful before API credentials are available and gives Phase 2 a concrete interface to implement real writes.

### Conversational compatibility target

The user's first case should be supported as a structured preview:

> 侯玉峰，浦江项目，开发chunkmoe；于家硕，浦江项目，SFT任务排队一天。

Expected structured shape:

- person: 侯玉峰
- project: 浦江项目
- work: 开发chunkmoe
- status: in_progress
- person: 于家硕
- project: 浦江项目
- work: SFT任务
- status: blocked_or_waiting
- blocker: 排队一天

Phase 1 does not need to mutate Plane for this case yet, but it must produce a confirmable change preview compatible with future Plane writes.

## Chosen Approach

Implement Phase 1 as a local connector toolkit:

1. `scripts/plane-health.sh` checks Plane HTTP reachability, Docker service status, and release/config basics without printing secrets.
2. `scripts/export-plane-timeline.sh` is hardened into a read-only extractor with stable JSONL and `SINCE` filtering.
3. `scripts/parse-progress-case.py` converts a simple Chinese progress update into structured events and a Plane change preview.
4. `PLANE-DATA-INTEGRATION.md` documents the read/write boundary, event schema, and source traceability.

## Risks

| Risk | Mitigation |
|---|---|
| Plane API auth may not be available non-interactively | Ship dry-run connector and documented token/session setup |
| Plane schema changes across versions | Keep SQL isolated to one script and include health/version output |
| Empty Plane data produces empty timeline | Treat empty export as valid and use the progress parser as a shape test |
| Natural language can be ambiguous | Phase 1 only supports preview; Phase 2 adds confirmation and clarification |

## Research Complete

The implementation path is clear: keep Plane as the visual source of truth, read PostgreSQL only for analytics, and prepare writes through an explicit connector boundary.

