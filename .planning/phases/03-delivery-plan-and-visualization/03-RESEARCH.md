# Phase 3 Research: Delivery Plan And Visualization

**Phase:** 03
**Date:** 2026-07-02
**Status:** Complete

## Research Question

How can the project visualize delivery state locally without adding new infrastructure?

## Findings

- Phase 1 and Phase 2 already create the needed source data: Plane timeline JSONL and progress audit JSON.
- A static HTML dashboard is sufficient for the first useful visualization and avoids a new server.
- A Markdown delivery plan is better than a database for this slice because it is inspectable, easy to back up later, and can be regenerated.
- The current data is sparse, so the dashboard must handle empty/unknown fields gracefully.

## Chosen Approach

Create `scripts/build-delivery-dashboard.py` to:

1. Load `exports/plane/timeline.jsonl`.
2. Load `exports/progress/*.json`.
3. Compute project, issue, people, blocker, stale, unresolved, and timeline views.
4. Write `exports/delivery/dashboard.json`.
5. Write `exports/delivery/delivery-plan.md`.
6. Write `exports/delivery/dashboard.html`.

## Verification Seed

The seed case should appear as:

- Project: `浦江`.
- Issue: `1-1 InternS2 SFT`.
- Person: `于家硕`.
- Blocker/waiting: `排队一天`.
- Draft risk: `chunkmoe` unresolved/manual-target.

## Research Complete

A static dashboard generator is the smallest useful Phase 3 implementation.

