---
phase: 5
plan: 1
subsystem: demand-triage-capability
tags:
  - demand
  - triage
  - capability
  - assignment
key-files:
  - scripts/triage-demand.py
  - PLANE-DATA-INTEGRATION.md
metrics:
  requirements_tested: 2
  bounced_examples: 1
  planned_changes: 1
  capability_people: 2
---

# Phase 5 Plan 1 Summary

## Result

Demand triage and lightweight capability matching are implemented.

`scripts/triage-demand.py` stores requirements, scores and ranks them, bounces unclear items, infers a capability matrix from progress/dashboard evidence, recommends assignees with reasoning, and emits planned Plane work-item draft changes.

## Commits

| Task | Commit | Description |
|---|---|---|
| 1 | `bb50e71` | Added demand triage CLI |
| 2 | `bb50e71` | Documented demand triage workflow |
| 3 | `bb50e71` | Ran clear and unclear demand examples |

## Verification Evidence

| Check | Evidence |
|---|---|
| Python compile | py_compile for `scripts/triage-demand.py` passed |
| Clear demand | `浦江项目需要新增chunkmoe性能优化任务，优先级高，影响SFT交付` produced `approved_draft` |
| Bounce-back | `做一下那个东西` produced `bounced` with clarification request |
| Capability matrix | Outputs include 2 people: 侯玉峰 and 于家硕 |
| Recommendation | Clear demand recommended 侯玉峰 with `skill_overlap=['chunkmoe']`, availability 5, blockers 0 |
| Plane changes | Clear demand produced one `create_plane_work_item_draft` planned change |

## Requirement Coverage

| Requirement | Status | Evidence |
|---|---|---|
| DEMD-01 | Passed | `demand-backlog.json` stores source, context, category, scores, status, and decision notes |
| DEMD-02 | Passed | Unclear demand is marked `bounced` with requested clarification |
| DEMD-03 | Passed | Demand scoring includes clarity, value, urgency, cost, risk, dependency, and strategic fit |
| DEMD-04 | Passed | Approved demand emits planned Plane work-item draft change |
| CAPA-01 | Passed | `capability-matrix.json` includes skills, work history, load, blockers, and availability |
| CAPA-02 | Passed | Recommendation includes assignee, confidence, and reasoning |

## Deviations from Plan

None - plan executed as written.

## Residual Risks

- Scoring is heuristic and should be calibrated with more real demand examples.
- Planned Plane work-item creation is not applied automatically; API-backed creation can be added after token/confirmation policy is settled.

## Self-Check: PASSED

All Phase 5 verification commands passed, and outputs remain under ignored `exports/`.
