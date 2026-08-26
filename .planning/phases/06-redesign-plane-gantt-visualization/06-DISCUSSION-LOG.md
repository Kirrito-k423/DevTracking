# Phase 6: Redesign Plane Gantt Visualization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-06
**Phase:** 06-redesign-plane-gantt-visualization
**Areas discussed:** Gantt view positioning, task hierarchy, event marker semantics, detail content, visual density

---

## Gantt View Positioning

| Option | Description | Selected |
|--------|-------------|----------|
| New view | Build a dedicated Gantt sidecar view and preserve existing dashboard output | ✓ |
| Replace existing dashboard | Make the old dashboard HTML become the Gantt surface | |
| Tune Plane native view | Continue adjusting Plane's built-in Gantt configuration | |

**User's choice:** 新视图。
**Notes:** The current Plane visualization is considered unusable for the desired delivery workflow.

---

## Task Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Plane parent_id | Use Plane parent-child relationships as the authoritative hierarchy | ✓ |
| Project/module grouping | Group by project or module before task parentage | |
| Hybrid synthetic grouping | Build a custom hierarchy that can diverge from Plane | |

**User's choice:** Plane `parent_id`.
**Notes:** Planner should treat parent-child relationships as source-of-truth, not infer a separate hierarchy unless data is missing.

---

## Event Marker Semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Plane-native evidence | Derive blocker/completion/milestone from Plane labels, state, and `completed_at` | ✓ |
| Progress events first | Derive markers primarily from daily-progress audit events | |
| Merged heuristics | Blend Plane and progress signals with heuristic precedence | |

**User's choice:** 阻塞、完成、里程碑标记应来自 Plane labels/state/completed_at。
**Notes:** Progress events may enrich text, but Plane-native data should drive marker semantics.

---

## Detail Content

| Option | Description | Selected |
|--------|-------------|----------|
| Delivery summary | Show operator-facing delivery status, owner, next action, date range, source links | ✓ |
| Evidence trace | Lead with raw source rows, event IDs, and audit details | |
| Split detail | Separate summary and evidence into equal-weight sections | |

**User's choice:** 交付摘要。
**Notes:** Source evidence is still needed, but should be secondary to the delivery summary.

---

## Visual Density

| Option | Description | Selected |
|--------|-------------|----------|
| High-density only | Optimize for daily scanning and compact rows | |
| Presentation only | Optimize for demo/report readability with larger rows | |
| Both modes | Default dense mode plus a presentation/reporting mode toggle | ✓ |

**User's choice:** 高密度表格和演示汇报都支持。
**Notes:** Default should be high-density for operation; presentation mode should reduce clutter without changing the underlying data.

---

## the agent's Discretion

- Choose exact implementation technique for static Gantt rendering and connector lines.
- Choose whether to extend the existing dashboard generator or add a focused Gantt generator.
- Choose exact output file names around the expected `exports/delivery/gantt.html` and structured Gantt JSON.

## Deferred Ideas

- Plane UI fork or internal Plane frontend changes.
- Large service/framework adoption unless static output cannot satisfy the required interactions.
