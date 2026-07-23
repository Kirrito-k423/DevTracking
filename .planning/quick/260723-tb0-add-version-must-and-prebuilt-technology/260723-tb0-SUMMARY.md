---
quick: 260723-tb0
date: 2026-07-23
status: complete
commit: b0a2bd4
---

# 双需求页面、事件新鲜度排序与任务 Pin 总结

## 完成内容

- 增加“版本必做”和“预埋技术”两个共享完整 Gantt 能力的需求页面。
- 历史任务在缺少分类字段时默认进入“版本必做”；新任务继承父任务分类，无父任务时进入当前页面。
- 任务详情可把当前任务及全部子任务整体移动到另一个页面，移动时重置旧页面的 Pin 槽位。
- 未 Pin 的同级任务按最近事件时间降序排列；父任务使用整棵子树的最新事件时间，保持父子任务连续。
- 每个任务行增加小型 Pin 按钮，固定当前同级槽位；取消后恢复自动排序。
- `demand_lane`、`pinned`、`pin_position` 已进入 localStorage、autosave、portable snapshot 和 changeset，不改动旧 schema 标识。

## 验证

- `python3 -m unittest discover -s tests -v`：10 项通过。
- 内联 JavaScript 语法检查和 `git diff --check` 通过。
- `http://127.0.0.1:8090/gantt.html`：HTTP 200，运行目录与仓库 HTML SHA-256 一致。
- 真实浏览器：运行快照恢复后版本必做显示 104 个任务和 104 个 Pin 控件；预埋技术可切换并显示空页面提示；返回后任务数量恢复，控制台无错误。
- 部署期间发现磁盘接近满载；只读分析识别约 29 GB 可再生缓存候选，未删除任何用户数据。
