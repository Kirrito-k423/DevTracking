---
status: complete
completed: 2026-07-13
commit: 9ef9830
---

# Quick Task 260713-kzq Summary: 修复公开 Gantt 的 JSON 导入导出

## What Changed

- 公开静态页面现在可直接导入其导出的 JSON 变化集。
- 本地服务继续支持 ZIP 迁移包导入。
- 文件选择器与拖放区域同时接受 `.json` 和 `.zip`。
- 移除了可移植页面中一次选择触发两次导入的调用。
- 可移植页面在没有服务端 API 时会回退读取同目录的快照 JSON。

## Verification

- 生成后的 Gantt JavaScript 语法检查通过。
- 当前 JSON 快照包含可恢复的 73 个任务和 71 个事件。
- 本地服务实际导入 ZIP 迁移包成功，并恢复 73 个任务和 71 个事件。
- 公开站点构建并重新发布成功。
