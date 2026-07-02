# Roadmap: Plane Demand Hub

**Created:** 2026-07-02
**Granularity:** Coarse
**Project mode:** Vertical MVP

## Overview

| Phase | Name | Goal | Requirements |
|-------|------|------|--------------|
| 1 | Plane Connector And Timeline Foundation | Make Plane safely readable and writable through supported paths, with normalized timeline export | PLANE-01..PLANE-05 |
| 2 | Conversational Progress To Plane | Convert daily natural-language progress updates into confirmed Plane updates | CONV-01..CONV-05 |
| 3 | Delivery Plan And Visualization | Maintain delivery state and show project/person/blocker/timeline views | DELV-01..DELV-05, VIS-01..VIS-04 |
| 4 | Reports, AI Context, And Backup | Generate daily/weekly/risk/retro reports and back up timeline/report artifacts | REPT-01..REPT-05, BACK-01..BACK-04 |
| 5 | Demand Triage And Capability Matching | Add requirement filtering, prioritization, and delivery-relevant capability matching | DEMD-01..DEMD-04, CAPA-01..CAPA-02 |

## Phases

### Phase 1: Plane Connector And Timeline Foundation
**Goal:** Establish a safe integration foundation: local Plane health, read-only timeline extraction, API-level write connector, and source traceability.
**Mode:** mvp
**Requirements:** PLANE-01, PLANE-02, PLANE-03, PLANE-04, PLANE-05
**UI hint:** no

**Success Criteria**:
1. A command verifies Plane is reachable at the configured local URL and reports version/config basics.
2. Timeline export reads projects, issues, comments, activities, states, and assignees without mutating Plane.
3. Exported JSONL has stable event schema and can be filtered by date.
4. A minimal Plane writer can create/update comments or work items through API-level behavior.
5. Integration docs explain read/write boundaries and source traceability.

### Phase 2: Conversational Progress To Plane
**Goal:** Let the user report multiple people's daily progress in natural language, preview structured changes, and apply confirmed updates to Plane.
**Mode:** mvp
**Requirements:** CONV-01, CONV-02, CONV-03, CONV-04, CONV-05
**UI hint:** yes

**Success Criteria**:
1. A daily progress message can be parsed into people, projects, work, blockers, risks, and next actions.
2. The system produces a human-readable change preview before writing.
3. Ambiguous person/project/task references are flagged for clarification.
4. Confirmed changes create Plane comments, status changes, follow-up tasks, or blocker notes.
5. Original message, parsed events, planned changes, and applied changes are stored for audit.

### Phase 3: Delivery Plan And Visualization
**Goal:** Maintain a live delivery plan and visualize project, person, blocker, risk, and timeline status.
**Mode:** mvp
**Requirements:** DELV-01, DELV-02, DELV-03, DELV-04, DELV-05, VIS-01, VIS-02, VIS-03, VIS-04
**UI hint:** yes

**Success Criteria**:
1. Active projects show milestones, key tasks, owners, blockers, and next review dates.
2. Stale work, unowned blockers, and drifting projects are detected.
3. The dashboard shows progress by project state, owner, blocker, risk, and recent activity.
4. A project timeline view is generated from Plane history.
5. People view shows current load, recent contribution evidence, and help-needed items.

### Phase 4: Reports, AI Context, And Backup
**Goal:** Generate source-backed daily, weekly, risk-help, and retrospective reports, then back up structured exports and reports.
**Mode:** mvp
**Requirements:** REPT-01, REPT-02, REPT-03, REPT-04, REPT-05, BACK-01, BACK-02, BACK-03, BACK-04
**UI hint:** yes

**Success Criteria**:
1. Daily report summarizes shipped work, changes, blockers, risks, and next actions.
2. Weekly report groups progress by project and person.
3. Risk-help summary names owner, blocker, needed help, urgency, and escalation path.
4. Project retrospective extracts key nodes, blockers, breakthroughs, contributors, and follow-up actions.
5. Timeline JSONL and Markdown reports can be exported and backed up without secrets.

### Phase 5: Demand Triage And Capability Matching
**Goal:** Extend the system upstream: requirements enter a filter/bounce/prioritization process and approved work is matched to people based on delivery-relevant capability and load.
**Mode:** mvp
**Requirements:** DEMD-01, DEMD-02, DEMD-03, DEMD-04, CAPA-01, CAPA-02
**UI hint:** yes

**Success Criteria**:
1. Imported requirements store source, context, category, priority, status, and decision notes.
2. Low-clarity or low-value requirements can be bounced back with reasons and requested clarification.
3. Requirements are ranked using value, urgency, cost, risk, dependencies, and strategic fit.
4. Approved requirements can create Plane projects or work items.
5. Capability matrix supports skills, history, load, and preferred task types.
6. Task recommendations include visible reasoning and confidence.

## Requirement Coverage

All 34 v1 requirements in `.planning/REQUIREMENTS.md` are mapped to exactly one phase.

---
*Roadmap created: 2026-07-02*

