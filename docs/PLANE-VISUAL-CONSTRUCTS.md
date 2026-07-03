# Plane 可视化构件

更新时间：2026-07-03

## 已构建内容

本项目在 Plane `teamwork / 浦江` 中构建了三类真实构件：

1. 标签：用于把关键阻塞、求助、里程碑、突破、每日事件标成可筛选对象。
2. 视图：用于在 Plane 原生页面上按不同管理问题查看同一批 work item。
3. 模块：用于按工作域组织交付主线。

可重复执行的构建命令：

```bash
cd /Users/Zhuanz/Documents/DevTracking
scripts/bootstrap-plane-visual-constructs.py
```

该命令通过 Plane 后端容器运行 Django 业务模型，幂等创建或修正构件，不会读取或打印 `plane.env` 中的 secret。

## 标签

| 标签 | 用途 |
|---|---|
| `blocked` | 关键阻塞，影响交付，需要解除 |
| `needs-help` | 需要协助、需要外部确认或资源 |
| `milestone` | 关键达成节点、验收点、里程碑 |
| `breakthrough` | 关键突破，例如性能、算法、工程方案突破 |
| `daily-event` | 每日事件，用于把口头日报落成可视化对象 |
| `owner:于家硕` | 临时人员标记，后续可替换为真实 assignee |
| `owner:侯玉峰` | 临时人员标记，后续可替换为真实 assignee |

## 视图

| 视图 | 布局 | 用途 |
|---|---|---|
| `Overview` | Gantt | 默认甘特总览，打开子任务显示 |
| `交付总览` | Gantt | 展示交付物、子任务、关键节点和突破 |
| `关键阻塞` | Kanban | 只看 `blocked` / `needs-help` |
| `关键节点` | Gantt | 只看 `milestone` / `breakthrough` |
| `每日事件` | List | 只看 `daily-event`，避免污染主交付视图 |

真实 Plane 页面：

| 视图 | 链接 |
|---|---|
| `Overview` | http://localhost:8090/teamwork/projects/e4924234-5afd-4954-989d-ac094fe75976/views/070f9a9d-21b7-4f8c-b21d-21c04d843366/ |
| `交付总览` | http://localhost:8090/teamwork/projects/e4924234-5afd-4954-989d-ac094fe75976/views/c81409b9-c430-4364-aaff-65ce5c0b0aff/ |
| `关键阻塞` | http://localhost:8090/teamwork/projects/e4924234-5afd-4954-989d-ac094fe75976/views/6950c3aa-b39b-4646-a214-9c36607ed854/ |
| `关键节点` | http://localhost:8090/teamwork/projects/e4924234-5afd-4954-989d-ac094fe75976/views/0fa17196-cfe5-40df-9b0a-86c3703d6d2f/ |
| `每日事件` | http://localhost:8090/teamwork/projects/e4924234-5afd-4954-989d-ac094fe75976/views/7850e5b6-393a-47aa-bd6e-7f5e528d74e6/ |

页面截图：

- `docs/assets/plane-overview-real-view.png`
- `docs/assets/plane-key-nodes-real-view.png`
- `docs/assets/plane-key-blockers-real-view.png`
- `docs/assets/plane-daily-events-real-view.png`
- `docs/assets/local-delivery-dashboard-latest.png`

## 模块

| 模块 | 状态 | 范围 |
|---|---|---|
| `SFT 交付` | in-progress | `InternS2 SFT` 主线和相关子任务 |
| `chunkmoe` | in-progress | `chunkmoe 性能优化` |
| `评测` | backlog | 后续评测、验收、效果回归 |

当前任务关系：

- `1-1 InternS2 SFT`
  - 标签：`milestone`, `owner:于家硕`
  - 模块：`SFT 交付`
- `1-2 chunkmoe 性能优化`
  - 父任务：`InternS2 SFT`
  - 标签：`breakthrough`, `owner:侯玉峰`
  - 模块：`SFT 交付`, `chunkmoe`
- `1-3 2026-07-02 侯玉峰：开发 chunkmoe`
  - 父任务：`chunkmoe 性能优化`
  - 标签：`daily-event`, `breakthrough`, `owner:侯玉峰`
  - 模块：`SFT 交付`, `chunkmoe`
- `1-4 2026-07-02 于家硕：SFT 排队等待资源`
  - 父任务：`InternS2 SFT`
  - 标签：`daily-event`, `blocked`, `needs-help`, `owner:于家硕`
  - 模块：`SFT 交付`

## 后续录入规则

把你每天告诉我的进展落到 Plane 时，按以下规则组织：

- 普通日报：创建 `daily-event` 子任务，日期设为当天。
- 关键阻塞：创建或更新 `blocked` + `needs-help` 工作项。
- 关键达成：创建 `milestone` 工作项，日期设为达成日。
- 关键突破：创建 `breakthrough` 工作项，挂到对应交付物或技术子任务下。
- 真实交付工作：创建普通技术子任务，不要用日报事件替代。

这样 Plane 原生 view 就能按标签、模块、父子关系和时间线把重点可视化出来。
