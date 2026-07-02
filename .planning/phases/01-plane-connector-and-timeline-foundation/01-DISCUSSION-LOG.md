# Phase 1: Plane Connector And Timeline Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-02
**Phase:** 1-Plane Connector And Timeline Foundation
**Areas discussed:** Plane health and configuration, read-only extraction, write boundary, source traceability, test data and real case strategy

---

## Plane health and configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Local Plane first | Use the existing self-hosted Plane at `http://localhost:8090` as the target | ✓ |
| Abstract config only | Design without validating the local deployment first | |

**User's choice:** Auto-selected recommended default.
**Notes:** Local Plane is already running and was previously verified with HTTP 200.

---

## Read-only extraction

| Option | Description | Selected |
|--------|-------------|----------|
| PostgreSQL read-only exporter | Read Plane history directly for analytics and AI context | ✓ |
| API-only reporting | Use only Plane API for all reporting reads | |

**User's choice:** Auto-selected recommended default.
**Notes:** Direct DB reads are complete and fast; they must remain read-only.

---

## Write boundary

| Option | Description | Selected |
|--------|-------------|----------|
| API-level writes | Use Plane API or controlled connector for normal writes | ✓ |
| Direct SQL writes | Insert/update Plane tables directly | |

**User's choice:** Auto-selected recommended default.
**Notes:** Direct SQL writes risk missing activity logs, permissions, notifications, sequence handling, and cache behavior.

---

## Source traceability

| Option | Description | Selected |
|--------|-------------|----------|
| Source-backed reports | Every report claim links to issue keys or timeline events | ✓ |
| Free-form summaries | Let AI summarize without event references | |

**User's choice:** Auto-selected recommended default.
**Notes:** Source-backed output is necessary for trustworthy daily, weekly, risk, and retrospective reports.

---

## Test data and real case strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve real case as acceptance scenario | Keep the 浦江项目 update as a target scenario for parser/write/report flows | ✓ |
| Ignore until later | Build generic plumbing without a concrete case | |

**User's choice:** User explicitly provided the case; auto-selected as acceptance scenario.
**Notes:** Case: 侯玉峰，浦江项目，开发chunkmoe；于家硕，浦江项目，SFT任务排队一天。

---

## the agent's Discretion

- Exact script names, package boundaries, and CLI flags.
- Whether the first writer connector is dry-run or real API-backed depends on available local API authentication.
- Minimal verification design, as long as read-only extraction is proven non-mutating.

## Deferred Ideas

- Full conversational progress parser belongs to Phase 2.
- Dashboard/person workload visualization belongs to Phase 3.
- Report generation belongs to Phase 4.
- Demand triage and capability matching belong to Phase 5.

