---
quick_id: 260716-gkw
status: complete
mode: quick-full
date: 2026-07-16
description: 为 Gantt 任务和事件新增底部资料绑定与预览栏，并让附件随 portable ZIP 迁移
must_haves:
  truths:
    - 点击任务条或事件后，详情和资料绑定区域从屏幕底部出现，不再从右侧出现
    - 支持通过按钮或拖拽上传 10MB 以内的 ZIP、图片、PPT、TXT、Word 文件并绑定到当前任务或事件
    - 图片附件可点击放大预览，其他附件可打开或下载，附件可删除
    - 附件元数据和二进制文件均可持久化，并随 portable ZIP 导出与导入
  artifacts:
    - scripts/build-delivery-dashboard.py
    - scripts/serve-delivery-dashboard.py
    - scripts/export-gantt-portable.py
    - tests/test_gantt_attachments.py
  key_links:
    - 浏览器上传接口写入 exports/delivery/gantt-attachments，changeset snapshot 保存绑定元数据
    - portable exporter 将 gantt-attachments 复制到 portable/gantt/latest，ZIP 下载与导入递归处理附件
---

# Quick Task 260716-gkw: Gantt 附件资料栏与 portable 迁移

## Task 1: 增加受控附件存储与 portable ZIP 数据链路

- files: `scripts/serve-delivery-dashboard.py`, `scripts/export-gantt-portable.py`
- action: 增加附件上传、读取、删除 API；校验允许类型与单文件 10MB 上限；portable 导出复制附件目录，ZIP 导入导出安全递归处理附件。
- verify: 服务端单元测试覆盖允许/拒绝上传、读取、删除，以及 portable 导入导出附件。
- done: 附件在刷新和跨机器 ZIP 迁移后仍可访问，路径遍历和超限文件会被拒绝。

## Task 2: 将详情改为底部资料绑定与预览栏

- files: `scripts/build-delivery-dashboard.py`
- action: 把右侧抽屉改为底部面板；为任务和事件显示各自附件，支持按钮选择、拖拽、上传进度、删除、下载以及图片全屏放大；附件元数据纳入 localStorage、autosave 和 changeset snapshot。
- verify: 生成页面 JavaScript 通过语法检查，关键 DOM、样式和 API 调用存在。
- done: 任务条和事件都能从底部面板完成附件的添加、查看和删除，10MB 限制在客户端清楚提示。

## Task 3: 构建、回归与可视化验收

- files: `tests/test_gantt_attachments.py`, `.planning/STATE.md`, 本任务 SUMMARY/VERIFICATION
- action: 补充测试，重建 delivery 页面，启动 8091 服务并进行桌面/移动视口交互检查；记录完成状态。
- verify: Python 编译、单元测试、生成 HTML 的 Node 语法检查、附件 API 冒烟测试和浏览器截图检查全部通过。
- done: 每条显式需求均有当前代码或运行时证据，服务可在 `http://127.0.0.1:8091/gantt.html` 直接体验。
