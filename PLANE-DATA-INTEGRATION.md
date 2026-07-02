# Plane 数据集成方案

## 判断

这个方案可行，但边界要清楚：

- 读 Plane 数据库：可行，适合报表、AI 历史上下文、时间线、备份校验。
- 直接修改 Plane 数据库：不建议，除非是一次性修复且先备份。Plane 有 Django 业务逻辑、权限、活动日志、通知、序号、软删除、缓存和外键约束，直接写库容易绕过这些逻辑。
- 写入 Plane：优先用 Plane API / Webhook / 官方导入能力。

## Phase 1 本地命令

### 健康检查

```bash
cd /Users/Zhuanz/Documents/DevTracking
scripts/plane-health.sh
```

该命令会检查：

- `http://localhost:8090` HTTP 可达性
- Docker Compose 服务运行状态
- Plane DB 是否能执行只读查询
- 当前配置的 Plane release

命令会加载 `plane-selfhost/plane-app/plane.env`，但不会打印密码、secret、token 或 raw env 值。

### 时间线导出

```bash
cd /Users/Zhuanz/Documents/DevTracking
scripts/export-plane-timeline.sh --since 2026-07-01T00:00:00Z --output exports/plane/timeline.jsonl
```

兼容旧用法：

```bash
SINCE=1970-01-01T00:00:00Z scripts/export-plane-timeline.sh exports/plane/timeline.jsonl
```

导出脚本在 PostgreSQL `begin read only` 事务中运行，只做读取，输出 JSONL 到被 `.gitignore` 排除的 `exports/`。

### 自然语言进展预览

```bash
scripts/parse-progress-case.py "侯玉峰，浦江项目，开发chunkmoe；于家硕，浦江项目，SFT任务排队一天。"
```

该命令只生成 dry-run 变更计划，不写 Plane。输出包含：

- `events`: 结构化人员、项目、任务、状态、阻塞信息
- `planned_plane_changes`: 后续可通过 Plane API 执行的评论、阻塞或跟进任务计划
- `source`: 原始输入与分段索引，供报告追溯

### Plane API 评论 writer

Plane v1.3.1 后端路由中，工作项评论创建/更新走：

```text
POST  /api/v1/workspaces/{workspace_slug}/projects/{project_id}/work-items/{issue_id}/comments/
PATCH /api/v1/workspaces/{workspace_slug}/projects/{project_id}/work-items/{issue_id}/comments/{comment_id}/
```

认证请求头是 `X-Api-Key`。本仓库提供的 writer 默认只 dry-run：

```bash
scripts/plane-api-comment.py \
  --workspace <workspace_slug> \
  --project-id <project_uuid> \
  --issue-id <issue_uuid> \
  --comment "侯玉峰：开发chunkmoe"
```

真正写入时必须显式设置 API key 并加 `--apply`：

```bash
PLANE_API_KEY=<redacted> scripts/plane-api-comment.py \
  --workspace <workspace_slug> \
  --project-id <project_uuid> \
  --issue-id <issue_uuid> \
  --comment "侯玉峰：开发chunkmoe" \
  --external-id manual-2026-07-02-001:segment:1 \
  --apply
```

不要把 `PLANE_API_KEY` 写进仓库、日志、报告或 GitHub 备份。

## 本地数据库位置

Plane 使用 Docker 内的 PostgreSQL：

```bash
cd /Users/Zhuanz/Documents/DevTracking
set -a
. plane-selfhost/plane-app/plane.env
set +a

docker compose \
  -f plane-selfhost/plane-app/docker-compose.yaml \
  --env-file plane-selfhost/plane-app/plane.env \
  exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" plane-db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

当前本地 Plane v1.3.1 的 public schema 有 110 张表。核心报表相关表：

| 数据 | 表 |
|---|---|
| 工作区 | `workspaces` |
| 项目 | `projects` |
| 工作项 | `issues` |
| 工作项状态 | `states` |
| 负责人 | `issue_assignees` + `users` |
| 评论/日报痕迹 | `issue_comments` |
| 状态/字段变更历史 | `issue_activities` |
| 周期 | `cycles` + `cycle_issues` |
| 模块 | `modules` + `module_issues` |
| 标签 | `labels` + `issue_labels` |
| GitHub 同步 | `github_issue_syncs`, `github_comment_syncs`, `github_repositories` |
| API 调用记录 | `api_activity_logs` |
| Webhook 记录 | `webhook_logs` |

## 报告可抽取的信息

### 项目进展

来自 `issues`、`states`、`issue_assignees`：

- 每个项目总工作项数
- 按状态分布
- 按负责人分布
- 高优先级未完成项
- 逾期项
- 本周新增、本周完成、本周仍阻塞

### 时间线

来自 `issue_activities`、`issue_comments`、`issues.completed_at`：

- 谁在什么时候创建了工作项
- 谁修改了状态、负责人、优先级、截止时间
- 谁评论了什么
- 哪些任务完成
- 哪些任务长期无更新

### AI 历史上下文

推荐导出成 JSONL，每行一个事件：

```json
{"event_time":"2026-07-02T10:00:00Z","event_type":"issue_activity","project":"Demo","issue_key":"DEMO-12","issue_title":"xxx","actor":"Alice","source":{"table":"issue_activities","id":"...","field":"state"},"payload":{"field":"state","old_value":"Todo","new_value":"Done"}}
```

然后按项目、日期、人员切片喂给 AI：

- 生成日报：过滤最近 24 小时事件。
- 生成周报：过滤最近 7 天，按项目/人员聚合。
- 生成复盘：过滤项目全周期，抽关键节点、阻塞、突破、贡献者。
- 生成历史时间线：按 `event_time` 排序，压缩成里程碑叙事。

## 写入策略

### 推荐

自研 Demand Hub 写入 Plane 时走 API：

- 创建项目
- 创建/更新工作项
- 添加评论
- 更新状态、优先级、负责人
- 创建周期/模块

Phase 1 的写入边界分三层：

| 模式 | 行为 | 是否改 Plane |
|---|---|---|
| `dry_run` | 解析自然语言，生成可确认的 Plane change set | 否 |
| `api` | 使用 Plane API/session/token 执行已确认的 change set | 是 |
| `manual` | 输出操作清单，由操作者在 Plane UI 中执行 | 是，由人执行 |

当前仓库只实现 `dry_run`。等 Plane API 认证方式确认后，Phase 2 再把 `planned_plane_changes` 接到真实 API writer。

Plane 官方 API 文档覆盖 Project、Work Item、Work Item Activity、Comments、Cycles、Modules、Intake、Time Tracking 等对象。

### 不推荐

不要直接 `insert/update issues` 来创建任务。风险包括：

- 没有自动创建 `issue_activities`
- 可能破坏 `sequence_id`
- 不触发通知、webhook、缓存刷新
- 字段格式变更时升级困难
- 软删除和权限状态不一致

## 建议架构

```text
Plane PostgreSQL --只读--> Extractor --JSONL/Parquet--> AI Context Store
       ^                                           |
       |                                           v
Plane API <--------- Demand Hub ---------- 报告/时间线/复盘生成
```

原则：

1. 从数据库读，速度快、完整、适合报表。
2. 通过 API 写，保留 Plane 的业务逻辑。
3. 自己的需求过滤、人力建模、日报复盘数据放在独立数据库。
4. 定期把抽取结果和生成报告导出到 GitHub。

## Source traceability

每个导出的事件都应能追溯到 Plane 内部来源：

| 字段 | 用途 |
|---|---|
| `issue_key` | 报告中给人读的工作项引用 |
| `issue_id` | API 或 DB 级别的稳定关联 |
| `source.table` | 来源表，例如 `issue_comments`、`issue_activities` |
| `source.id` | 来源行 ID |
| `source.field` | 字段级变更来源，适用于 activity |
| `payload` | 事件细节，例如评论、状态变更、负责人、周期、模块、标签 |

报告和 AI 总结必须基于这些字段生成可核查结论。例如“于家硕的 SFT 任务排队一天”应能追溯到原始用户消息分段或后续 Plane 评论/活动事件。
