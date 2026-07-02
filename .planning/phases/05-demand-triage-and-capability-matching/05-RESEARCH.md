# Phase 5 Research: Demand Triage And Capability Matching

**Phase:** 05
**Date:** 2026-07-02
**Status:** Complete

## Finding

The first useful upstream demand layer can be local and heuristic. It does not require a separate database yet: generated JSON/Markdown under `exports/demand/` is enough to prove intake, ranking, bounce-back, and people recommendation behavior.

## Chosen Approach

Create `scripts/triage-demand.py` to:

- accept one or more requirements,
- score and classify them,
- bounce unclear items,
- infer capability matrix from progress/dashboard evidence,
- recommend assignees with reasoning,
- emit planned Plane changes for approved items.

## Research Complete

No new infrastructure is needed for Phase 5.

