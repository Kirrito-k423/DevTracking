# Phase 2 Research: Conversational Progress To Plane

**Phase:** 02
**Date:** 2026-07-02
**Status:** Complete

## Research Question

How should the project turn a Chinese daily progress sentence into safe, traceable Plane updates using the Phase 1 connector foundation?

## Findings

### Existing foundation

Phase 1 already provides:

- `scripts/parse-progress-case.py`: seed parser for semicolon-separated Chinese updates.
- `scripts/export-plane-timeline.sh`: source-backed Plane timeline JSONL with workspace slug, project ID, issue ID, issue key, title, source, and payload.
- `scripts/plane-api-comment.py`: Plane API comment writer, dry-run by default, real mutation only with `PLANE_API_KEY` and `--apply`.

### Practical Phase 2 shape

The shortest useful loop is an orchestration script:

1. Accept a natural-language progress message.
2. Parse it into structured progress events.
3. Load recent Plane timeline data.
4. Resolve project aliases and likely work-item targets.
5. Produce a readable preview and machine-readable change set.
6. Write an audit artifact under `exports/progress/`.
7. Optionally apply resolvable comment changes through Plane API.

This fits the user's desired interaction: the user talks to Codex, Codex runs the local workflow and shows what would change.

### Matching strategy

Use conservative deterministic matching first:

- Project: exact match against project names and aliases, including removing `项目`.
- Issue: exact issue key, exact/substring title, then ASCII token matching for terms like `SFT`.
- Ambiguity: if multiple targets match with similar confidence, do not apply.
- Missing target: keep as draft/proposed work item or project-level note.

This is safer than using an LLM to guess Plane targets silently.

### Apply strategy

Only comments should be applied in this phase:

- A progress event with a resolved issue can create a Plane comment.
- Waiting/blocker context can be included in the same comment.
- Follow-up tasks and status changes should remain planned changes until the target/action is explicit.

This satisfies the first conversational write loop while keeping risk low.

## Chosen Approach

Add a shared progress library plus orchestration CLI:

- `scripts/progress_lib.py`: parsing, aliases, matching, preview/change-set helpers.
- `scripts/parse-progress-case.py`: keep as a simple parser CLI, backed by the shared library.
- `scripts/progress-to-plane.py`: end-to-end preview/apply/audit command.
- `PLANE-DATA-INTEGRATION.md`: document the new conversational command.

## Verification Seed

Use the user's message:

```text
侯玉峰，浦江项目，开发chunkmoe；于家硕，浦江项目，SFT任务排队一天。
```

Expected result against current local Plane:

- Two progress events.
- `浦江项目` resolves to Plane project `浦江`.
- `SFT任务` resolves to existing work item `InternS2 SFT`.
- `chunkmoe` remains unresolved if no matching work item exists.
- Preview lists one apply-ready comment and one unresolved draft.
- Audit JSON is written under `exports/progress/`.

## Research Complete

Phase 2 can be implemented without new infrastructure by composing the Phase 1 scripts into a conservative local workflow.

