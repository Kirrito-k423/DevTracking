# Phase 6 Research: Redesign Plane Gantt Visualization

**Phase:** 06
**Date:** 2026-07-06
**Status:** Complete

## Finding

Phase 6 can stay local-first and static-file based. The existing static dashboard generator proves the output pattern, but its current JSON model is not rich enough for a collapsible Gantt view because issue rows do not carry `parent_id`, current date range, or aggregated labels/modules.

The needed source evidence already exists in the project, but it is split across artifacts:

- `scripts/export-plane-timeline.sh` exports `issue_created`, `issue_activity`, `issue_completed`, `label_added`, and `module_linked` timeline rows.
- Timeline `issue_activity` rows include `field: parent`, `field: start_date`, and `field: target_date` changes.
- Timeline `label_added` rows include labels such as `blocked`, `needs-help`, `milestone`, `daily-event`, and owner labels.
- Timeline `issue_completed` rows expose `completed_at` through the source field and completion event time.
- `scripts/apply-plane-daily-record.py` already writes and returns `parent_id`, `start_date`, `target_date`, labels, modules, and state for controlled daily-record writes.
- `exports/delivery/dashboard.json` currently aggregates issue state, priority, people, blockers, unresolved drafts, stale work, and recent activity, but not the hierarchy/date fields required for Gantt rendering.

## Chosen Approach

Build Phase 6 as a focused Gantt sidecar, not as a Plane UI fork and not as a replacement for all existing delivery dashboard outputs.

Recommended implementation shape:

1. Extend or complement `scripts/build-delivery-dashboard.py` with a Gantt model builder.
2. Produce `exports/delivery/gantt.json` with normalized task/event rows.
3. Produce `exports/delivery/gantt.html` with static HTML/CSS/JavaScript interactions.
4. Preserve existing `dashboard.html`, `dashboard.json`, and `delivery-plan.md` outputs.

## Data Model Requirements

`gantt.json` should include:

- `tasks[]`
  - `id`
  - `issue_id`
  - `issue_key`
  - `title`
  - `compact_label` capped at 8 visible characters
  - `parent_id`
  - `children[]` or child IDs
  - `depth`
  - `order`
  - `project`
  - `state`
  - `progress`
  - `owner`
  - `labels[]`
  - `modules[]`
  - `start_date`
  - `target_date`
  - `source_refs[]`
- `events[]`
  - `id`
  - `task_id`
  - `type` as `blocked`, `completed`, or `milestone`
  - `compact_label` capped at 8 visible characters
  - `date`
  - `summary`
  - `source_refs[]`

Plane-native event precedence is locked:

1. `blocked`: label `blocked`, label `needs-help`, or Plane state that clearly indicates blocked/waiting.
2. `completed`: `issue_completed`, `completed_at`, or completed state.
3. `milestone`: label `milestone`.

Progress audit events may enrich detail summaries but should not override the Plane-native classification above.

## Rendering Requirements

The static Gantt UI should use:

- a left sticky task table and right scrollable timeline grid,
- row-based rendering so table and bars stay vertically aligned,
- CSS/SVG/absolutely positioned connector lines between parent and child rows,
- click handlers for parent bar expand/collapse,
- click handlers for task bars and event markers opening a detail drawer/panel,
- density toggle that switches between dense daily-operation mode and presentation mode.

No heavy frontend framework is required for the MVP. A small static JavaScript module inside generated HTML or beside it is enough.

## Implementation Risks

### Current Timeline Export May Need Current-State Fields

`export-plane-timeline.sh` currently emits changes and events. Reconstructing final parent/date/label state from event history is possible, but fragile if the timeline window starts after an older change. The safer plan is to extend the export or dashboard builder to include current issue fields from Plane:

- `parent_id`
- `start_date`
- `target_date`
- current labels
- current modules
- current assignees or owner labels

If the export remains event-only, the Gantt builder must document that historical reconstruction depends on a sufficiently old `--since` value.

### Connector Lines Need Deterministic Geometry

Connector lines should be computed from row index, depth, and bar positions after expand/collapse filtering. Avoid trying to infer geometry from rendered text width.

### Labels Must Be Data-Enforced

The 8-character summary rule should be enforced in generated `compact_label` fields. CSS clipping can be an additional guard, not the only enforcement.

## Validation Architecture

Phase 6 should verify all of the following:

1. Run the existing export/dashboard flow and then the Gantt generator.
2. Assert `exports/delivery/gantt.json` exists and includes at least one parent-child relationship from Plane `parent` data.
3. Assert every task and event with visible text has `compact_label` length capped at 8 visible characters.
4. Assert `gantt.json` includes blocked, completed, and milestone event marker types when source evidence exists.
5. Assert `exports/delivery/gantt.html` includes expand/collapse controls, marker click handlers, density mode controls, and a detail panel.
6. Open the HTML locally or parse it to confirm it references `gantt.json` or embeds equivalent Gantt data.

## Research Complete

Phase 6 can be planned as one vertical MVP: enrich Gantt data, render static interactive HTML, document the command, and verify with existing local exports. No new persistent service or Plane frontend fork is needed.
