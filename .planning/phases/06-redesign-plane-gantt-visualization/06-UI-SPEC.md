---
phase: 06
slug: redesign-plane-gantt-visualization
status: approved
shadcn_initialized: false
preset: none
created: 2026-07-06
---

# Phase 06 - UI Design Contract

> Visual and interaction contract for the Phase 6 Gantt sidecar. Generated for local static HTML output and verified against the Phase 6 context decisions.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none |
| Icon library | CSS text symbols only for this static MVP |
| Font | system UI stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` |

The UI is an operational delivery surface, not a marketing page. It should feel compact, reliable, and scan-friendly. Avoid decorative hero sections, nested cards, oversized headings, gradient backgrounds, and one-note color themes.

---

## Information Architecture

| Region | Purpose | Contract |
|--------|---------|----------|
| Header band | File title, generated time, source counts, density toggle | One compact row on desktop; wraps cleanly on narrow screens |
| Toolbar | Density mode, project/module filters if implemented, expand/collapse all | Icon or short text controls with stable dimensions |
| Left task table | Task key, 8-character label, owner, state, date range | Sticky left column is preferred for horizontal timeline scroll |
| Right timeline grid | Gantt bars, dependency connectors, event markers | Synchronized row height with left table |
| Detail drawer/panel | Delivery summary for clicked task/event | Opens without navigating away; source evidence secondary |

---

## Gantt Interaction Contract

| Interaction | Required Behavior |
|-------------|-------------------|
| Parent task bar click | Toggle child task expansion/collapse |
| Expand/collapse affordance | Visible chevron or equivalent next to parent task label |
| Collapsed parent | Show rolled-up date range and progress/status summary |
| Connector lines | Draw visible parent-child relationship lines that remain aligned during expand/collapse and horizontal scroll |
| Task detail | Clicking a task row or bar opens delivery summary details |
| Event detail | Clicking an event marker opens marker-specific details |
| Keyboard fallback | Details must be reachable via focus + Enter or click-compatible button elements |

---

## Event Marker Contract

| Event | Visual | Source Semantics | Click Detail |
|-------|--------|------------------|--------------|
| Blocked | Red circled cross | Plane labels/state: `blocked`, `needs-help`, waiting/blocker state when available | Blocker summary, owner, task, needed help, source refs |
| Completed | Green dot | Plane state/completion evidence, especially `completed_at` or completed state | Completion summary, completion time, source refs |
| Milestone | Yellow star | Plane label `milestone` | Milestone title, date, parent task, source refs |

Progress audit data can enrich marker details, but Plane labels/state/`completed_at` drive marker classification.

---

## 8-Character Summary Contract

| Surface | Default Text Rule | Full Text Access |
|---------|-------------------|------------------|
| Task bar | Display at most 8 visible characters from the task summary/title | Detail panel and hover title |
| Event marker label | Display at most 8 visible characters when a label is shown | Detail panel and hover title |
| Left task table | May show task key plus 8-character compact label | Detail panel |

Use deterministic truncation. Do not rely on CSS clipping alone as the only enforcement; generated data should include compact labels.

---

## Density Modes

| Mode | Default | Row Height | Typography | Use Case |
|------|---------|------------|------------|----------|
| Dense | yes | 28-32px target | Compact labels, 12-13px table text | Daily operation and scanning |
| Presentation | no | 44-56px target | Larger labels, 14-16px text | Demo, review, and reporting |

The density toggle must not change the underlying task/event data. It changes only layout density, label prominence, and visual clutter.

---

## Spacing Scale

Declared values must be multiples of 4:

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, marker gaps, connector offsets |
| sm | 8px | Cell padding, toolbar gaps |
| md | 16px | Panel padding, section spacing |
| lg | 24px | Header band padding |
| xl | 32px | Major vertical separation |

Exceptions: none

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 13px dense, 15px presentation | 400 | 1.4 |
| Label | 12px dense, 13px presentation | 600 | 1.2 |
| Heading | 18px | 650 | 1.25 |
| Display | 22px | 700 | 1.2 |

Do not scale font size with viewport width. Letter spacing must remain `0`.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#f7f8fa` | Page background |
| Secondary (30%) | `#ffffff` | Table, header, detail surfaces |
| Accent (10%) | `#2f6fed` | Active timeline bars, focused selection, primary affordances |
| Destructive | `#c43d3d` | Blocked marker only |
| Success | `#1b8a5a` | Completed marker only |
| Milestone | `#b26b00` | Milestone star only |
| Line | `#d9dee7` | Table borders, grid, connector lines |
| Text | `#20242a` | Primary copy |
| Muted Text | `#657282` | Metadata and source hints |

Accent reserved for: active task bars, selected row/bar outline, density toggle active state, keyboard focus.

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Page title | Plane Demand Hub Gantt |
| Primary CTA | Refresh exports |
| Dense toggle | Dense |
| Presentation toggle | Present |
| Empty state heading | No Gantt data |
| Empty state body | Run the timeline and progress export commands, then rebuild the Gantt view. |
| Error state | Could not build Gantt data. Check the source path shown below and rerun the export command. |
| Detail heading fallback | Delivery summary |
| Source section heading | Source evidence |

Visible UI text should describe the current data and actions. Do not add in-app tutorial prose that explains implementation details.

---

## Responsive Contract

| Viewport | Behavior |
|----------|----------|
| Desktop | Sticky left task table plus horizontally scrollable timeline grid |
| Tablet | Keep table and timeline; allow horizontal timeline scroll |
| Mobile | Preserve functionality through horizontal scroll; text must not overlap controls |

Fixed-format elements such as row height, marker size, toolbar buttons, and timeline ticks must have stable dimensions to prevent layout shifts when labels change.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required |
| third-party registry | none | not allowed for this MVP without explicit review |

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-07-06
