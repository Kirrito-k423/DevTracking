# Research Summary: Plane Demand Hub

## Key Findings

**Stack:** Plane should be used as the visual project/task source of truth, with a Python sidecar for extraction, parsing, reporting, and API writes.

**Table Stakes:** Read Plane history, parse conversational progress, write confirmed changes to Plane, visualize status, and generate daily/weekly/retrospective reports.

**Watch Out For:** Do not directly mutate Plane PostgreSQL for normal operations. Keep custom Demand Hub state separate and preserve source traceability for every AI-generated claim.

## Recommended Strategy

Build the minimum useful closed loop first:

1. Extract Plane timeline.
2. Parse daily progress messages.
3. Preview intended Plane updates.
4. Write comments/status/follow-ups to Plane.
5. Generate visual and textual reports from the resulting history.

Demand import, filtering, prioritization, and capability matching should follow after the progress loop proves valuable.

