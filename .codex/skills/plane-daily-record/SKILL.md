---
name: plane-daily-record
description: Turn natural-language team daily progress into structured Plane work items, labels, modules, timeline/report refreshes, and verification. Use when the user gives daily updates, blockers, breakthroughs, completed work, validation needs, or asks how daily records should land on the local Plane board.
---

# Plane Daily Record

## Workflow

Use this skill to convert a daily update into real Plane state for the local Plane Demand Hub project.

1. Normalize the record date. Use Asia/Shanghai today unless the text gives a date.
2. Split the update into atomic events by project/workstream: one blocked event, one completed milestone, one breakthrough, or one follow-up validation task per Plane work item.
3. Infer the parent work item:
   - SFT, InternS2, 保存权重, 权重保存 -> `sft`
   - chunkmoe, chunk moe, 显存收益, 首步 NaN -> `chunkmoe`
   - 评测, 消融, 精度, 性能验证 -> parent `chunkmoe`, module `评测` when the validation is for chunkmoe
4. Infer temporary owner labels when no person is supplied:
   - SFT-related -> `owner:于家硕`
   - chunkmoe-related -> `owner:侯玉峰`
5. Classify labels:
   - Always add `daily-event` for content derived from a daily note.
   - Add `blocked` and `needs-help` for 卡住, 阻塞, 等待, 排队, 失败, or unknown external dependency.
   - Add `breakthrough` for 收益, 突破, 修复, NaN fixed, 性能/显存 improvement.
   - Add `milestone` for 完成, 交付, 验收点, or validation gates that decide readiness.
6. Choose state and priority:
   - Blocked/waiting event -> `todo`, priority `high`.
   - In-progress reproduction/debugging -> `in_progress`, priority `high` when it blocks delivery.
   - Completed feature/fix event -> `done` or `in_progress` if follow-up validation remains.
   - Follow-up validation -> `todo`, priority `high` if it gates merge or release.
7. Apply with the controlled script, not direct SQL:

```bash
scripts/apply-plane-daily-record.py \
  --date YYYY-MM-DD \
  --source-id daily-YYYYMMDD \
  --raw-text "用户原始日报文本" \
  --events-json '[{"external_id":"stable-id","title":"...","description":"...","parent":"sft","state":"todo","priority":"high","labels":["daily-event"],"modules":["SFT 交付"]}]'
```

The script writes or updates `exports/progress/<source-id>.json` as AI/report evidence when `--raw-text` is provided.

8. Refresh derived artifacts after applying, in this order:

```bash
scripts/export-plane-timeline.sh --since 1970-01-01T00:00:00Z --output exports/plane/timeline.jsonl
scripts/build-delivery-dashboard.py --timeline exports/plane/timeline.jsonl --progress-dir exports/progress --output-dir exports/delivery
scripts/generate-delivery-reports.py --dashboard exports/delivery/dashboard.json --output-dir exports/reports
```

## Plane Mapping

Use these real Plane constructs:

| Construct | Purpose |
|---|---|
| `每日事件` view | all `daily-event` work items |
| `关键阻塞` view | `blocked` or `needs-help` work items |
| `关键节点` view | `milestone` or `breakthrough` work items |
| `SFT 交付` module | SFT mainline and its blockers |
| `chunkmoe` module | chunkmoe implementation and optimization |
| `评测` module | ablation, accuracy, performance, validation |

Keep daily evidence as Plane work items, not only comments, whenever the user wants visualization on views.

## Output Back To User

After applying, report:

- Structured interpretation: events, labels, parents, state, priority.
- Plane issue keys created or updated.
- Which Plane views now show the items.
- Any uncertainty, especially owner/person inference.
