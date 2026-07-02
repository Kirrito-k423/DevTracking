# Pitfalls Research: Plane Demand Hub

## Pitfalls

| Pitfall | Warning Sign | Prevention | Phase |
|---------|--------------|------------|-------|
| Direct DB writes corrupt Plane state | Missing activities, broken sequence IDs, no notifications | Use DB read-only; write via Plane API | 1 |
| Building too much custom UI too early | Duplicating Plane screens before progress flow works | Use Plane views first, dashboard only for missing analytics | 1-3 |
| AI summaries lose source traceability | Reports make claims without event references | Store timeline event IDs and source issue keys | 2-4 |
| Ambiguous daily updates create wrong tasks | User says "张三推进了接口" with no project/task mapping | Produce a change preview or ask clarification | 2 |
| Capability model becomes HR surveillance | Skills/loads become broad performance scoring | Scope to task fit, load, blockers, and contribution evidence | 5 |
| Reports become verbose noise | Daily/weekly summaries repeat every task detail | Use sections: shipped, changed, blocked, risk, next actions | 4 |
| Plane upgrade breaks SQL assumptions | Column/table changes after version upgrade | Keep extractor tests and schema snapshot checks | 1 |

