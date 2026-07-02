# Phase 5: Demand Triage And Capability Matching - Context

**Gathered:** 2026-07-02
**Status:** Ready for planning
**Mode:** auto

<domain>
## Phase Boundary

Phase 5 adds the upstream intake layer: imported requirements can be classified, bounced back if unclear, prioritized, converted into planned Plane changes, and matched to people using lightweight delivery evidence from progress audits.

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build a local CLI first: `scripts/triage-demand.py`.
- **D-02:** Store generated demand backlog, triage report, capability matrix, and planned Plane changes under ignored `exports/demand/`.
- **D-03:** Use transparent heuristic scoring for value, urgency, cost, risk, dependencies, and strategic fit.
- **D-04:** Low clarity or too-short requirements should be bounced back with requested clarification.
- **D-05:** Capability matrix should be inferred from progress audit people/work evidence for this MVP.
- **D-06:** Approved/qualified requirements should produce planned Plane work-item changes, not direct writes.
- **D-07:** Recommendations must include reasoning and confidence.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — `DEMD-01..DEMD-04`, `CAPA-01..CAPA-02`.
- `.planning/ROADMAP.md` — Phase 5 scope.
- `exports/progress/*.json` — People/work evidence.
- `exports/delivery/dashboard.json` — People/blocker/current load evidence.
- `scripts/progress-to-plane.py` — Existing planned-change/audit style.

</canonical_refs>

<code_context>
## Existing Code Insights

- All prior operational scripts are Python stdlib.
- Generated artifacts go under ignored `exports/`.
- Plane writes are planned/API-gated, not direct SQL.

</code_context>

<specifics>
## Specific Ideas

- The seed people evidence should infer 侯玉峰 has `chunkmoe`/development context and 于家硕 has `SFT` context but is currently blocked/waiting.

</specifics>

<deferred>
## Deferred Ideas

- Full HR system.
- Learning from GitHub/Slack signals.
- Automatic creation of Plane work items without API key and confirmation.

</deferred>

---

*Phase: 05-Demand Triage And Capability Matching*
*Context gathered: 2026-07-02*

