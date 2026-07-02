# Requirements: Plane Demand Hub

**Defined:** 2026-07-02
**Core Value:** Turn natural-language team progress into trustworthy Plane state, visual timelines, and delivery reports without making every contributor do heavy manual bookkeeping.

## v1 Requirements

### Plane Integration

- [ ] **PLANE-01**: Operator can verify the local Plane instance is reachable and see its configured URL/version.
- [ ] **PLANE-02**: System can read Plane projects, issues, states, comments, activities, assignees, cycles, and modules from PostgreSQL without mutating Plane tables.
- [ ] **PLANE-03**: System can export a normalized JSONL timeline from Plane history with event time, event type, project, issue key, title, actor, and payload.
- [ ] **PLANE-04**: System can create or update Plane work items and comments through an API-level connector rather than direct SQL writes.
- [ ] **PLANE-05**: System records enough source references for each generated report claim to trace back to Plane issues, comments, or activities.

### Conversation Progress Loop

- [ ] **CONV-01**: User can provide a natural-language daily update describing multiple people, projects, completed work, blockers, risks, and next actions.
- [ ] **CONV-02**: System parses the update into structured progress events grouped by person, project, issue, blocker, and next action.
- [ ] **CONV-03**: System detects ambiguous updates and asks for clarification or produces a draft instead of silently writing uncertain changes.
- [ ] **CONV-04**: System can convert confirmed progress events into Plane comments, status updates, new follow-up tasks, or blocker markers.
- [ ] **CONV-05**: System keeps an audit trail of the original user message, parsed events, planned Plane changes, and applied Plane changes.

### Delivery Maintenance

- [ ] **DELV-01**: System maintains a delivery plan that maps active projects to milestones, key tasks, owners, blockers, and next review dates.
- [ ] **DELV-02**: System identifies stale work items with no recent activity.
- [ ] **DELV-03**: System identifies unowned blockers or risks that need help.
- [ ] **DELV-04**: System can suggest next actions for blocked or drifting projects.
- [ ] **DELV-05**: System can show per-person workload and contribution evidence using Plane assignments and activity history.

### Visualization

- [ ] **VIS-01**: User can view project progress by state, owner, blocker, risk, and recent activity.
- [ ] **VIS-02**: User can view a project timeline built from issue creation, updates, comments, state changes, and completions.
- [ ] **VIS-03**: User can view a people dashboard showing recent contributions, current load, blockers owned, and help needed.
- [ ] **VIS-04**: Visualizations link back to Plane issues or source events.

### Reports And AI Context

- [ ] **REPT-01**: System can generate a daily report from the latest progress events and Plane timeline.
- [ ] **REPT-02**: System can generate a weekly report grouped by project, person, shipped work, blockers, risks, and next actions.
- [ ] **REPT-03**: System can generate risk-help summaries with owner, blocker, needed help, urgency, and suggested escalation path.
- [ ] **REPT-04**: System can generate project retrospectives covering key nodes, blockers, breakthroughs, contributors, and follow-up actions.
- [ ] **REPT-05**: System can provide AI with bounded historical context for a project/person/time window without exposing secrets.

### Backup And Recovery

- [ ] **BACK-01**: System can export timeline JSONL and generated Markdown reports to local files.
- [ ] **BACK-02**: System can commit or push selected exports to a GitHub backup repository.
- [ ] **BACK-03**: System excludes Plane secrets, tokens, and raw `plane.env` from backups.
- [ ] **BACK-04**: System documents how to restore or rehydrate reports from exported timeline data.

### Demand And Capability Expansion

- [ ] **DEMD-01**: System can store imported requirements with source, customer/context, category, priority, status, and decision notes.
- [ ] **DEMD-02**: System can filter and bounce back unclear or low-value requirements with a reason and requested clarification.
- [ ] **DEMD-03**: System can rank requirements by value, urgency, cost, risk, dependency, and strategic fit.
- [ ] **DEMD-04**: System can turn approved requirements into Plane projects or work items.
- [ ] **CAPA-01**: System can maintain a lightweight capability matrix for people, including skills, project history, current load, and preferred task types.
- [ ] **CAPA-02**: System can recommend task assignees with visible reasoning and confidence.

## v2 Requirements

### Integrations

- **INTG-01**: Integrate Slack or chat channels for direct progress intake.
- **INTG-02**: Integrate GitHub commits, issues, and pull requests as extra progress signals.
- **INTG-03**: Generate Excel and PowerPoint versions of weekly and retrospective reports.
- **INTG-04**: Support multi-workspace Plane deployments.

### Automation

- **AUTO-01**: Run scheduled report generation without manual command execution.
- **AUTO-02**: Send report digests to configured channels.
- **AUTO-03**: Trigger risk-help workflows when blockers pass age or severity thresholds.

## User Stories

- As the operator, I can say "今天张三完成了登录接口，李四卡在权限模型，需要王五确认需求" and get a structured preview of Plane updates.
- As the operator, I can approve the preview and have Plane comments/tasks/statuses updated.
- As the operator, I can ask for "今天的日报" and receive a source-backed summary from Plane history.
- As the operator, I can ask for "这个项目的复盘" and get key nodes, blockers, breakthroughs, contributors, and next actions.
- As the operator, I can open a dashboard and see project state, person load, blockers, and timeline without manually assembling spreadsheets.

## Acceptance Criteria

- Every automated Plane write is traceable to an original user message or system decision.
- Every generated report links claims to Plane issue keys or timeline events.
- Ambiguous updates do not silently mutate Plane.
- The extractor can run repeatedly without changing Plane data.
- Secrets and tokens are never written to GitHub exports.

## Definition of Done

- Plane local deployment remains reachable at `http://localhost:8090`.
- Extractor, parser, writer, reports, dashboard, and backup flows are documented and verified.
- v1 requirements are mapped to roadmap phases.
- The first end-to-end demo can process a daily update, write to Plane, export timeline data, and generate a report.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Rebuilding Plane UI | Plane already solves attractive project/task UX |
| Direct Plane DB writes | Unsafe for activity logs, permissions, notifications, and upgrades |
| Full HR system | v1 only needs delivery-relevant capability and load signals |
| Public SaaS deployment | Local-first single workspace is the initial target |
| Fully autonomous writes without review | Ambiguous natural language needs confirmation safeguards |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLANE-01 | Phase 1 | Pending |
| PLANE-02 | Phase 1 | Pending |
| PLANE-03 | Phase 1 | Pending |
| PLANE-04 | Phase 1 | Pending |
| PLANE-05 | Phase 1 | Pending |
| CONV-01 | Phase 2 | Pending |
| CONV-02 | Phase 2 | Pending |
| CONV-03 | Phase 2 | Pending |
| CONV-04 | Phase 2 | Pending |
| CONV-05 | Phase 2 | Pending |
| DELV-01 | Phase 3 | Pending |
| DELV-02 | Phase 3 | Pending |
| DELV-03 | Phase 3 | Pending |
| DELV-04 | Phase 3 | Pending |
| DELV-05 | Phase 3 | Pending |
| VIS-01 | Phase 3 | Pending |
| VIS-02 | Phase 3 | Pending |
| VIS-03 | Phase 3 | Pending |
| VIS-04 | Phase 3 | Pending |
| REPT-01 | Phase 4 | Pending |
| REPT-02 | Phase 4 | Pending |
| REPT-03 | Phase 4 | Pending |
| REPT-04 | Phase 4 | Pending |
| REPT-05 | Phase 4 | Pending |
| BACK-01 | Phase 4 | Pending |
| BACK-02 | Phase 4 | Pending |
| BACK-03 | Phase 4 | Pending |
| BACK-04 | Phase 4 | Pending |
| DEMD-01 | Phase 5 | Pending |
| DEMD-02 | Phase 5 | Pending |
| DEMD-03 | Phase 5 | Pending |
| DEMD-04 | Phase 5 | Pending |
| CAPA-01 | Phase 5 | Pending |
| CAPA-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0

---
*Requirements defined: 2026-07-02*
*Last updated: 2026-07-02 after initialization*

