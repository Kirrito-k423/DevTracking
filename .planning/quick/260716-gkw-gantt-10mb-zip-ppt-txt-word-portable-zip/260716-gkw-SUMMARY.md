---
quick_id: 260716-gkw
status: complete
completed_at: "2026-07-16T04:18:32Z"
code_commit: c98ff65
---

# Quick Task 260716-gkw Summary

Gantt 任务和事件详情已从右侧抽屉改为屏幕底部资料工作栏。桌面端以详情/资料双栏显示，移动端把资料区优先放在详情字段之前。

## Delivered

- 任务和事件都可绑定 ZIP、PNG/JPG/GIF/WebP/BMP、PPT/PPTX、TXT、DOC/DOCX。
- 支持按钮多选和拖拽上传，浏览器与服务端均执行单文件 10MB 限制。
- 图片附件显示缩略图并可点击进入全屏放大预览；其他附件可下载；所有附件可删除。
- 附件二进制保存在 `gantt-attachments/`，绑定元数据进入 localStorage、autosave、changeset snapshot 和删除审计。
- portable 导出复制被引用附件并递归写入 ZIP；导入校验路径、大小、元数据、缺失/额外文件后恢复到 portable 与运行目录。
- 桌面安装版种子快照和 PyInstaller 打包会携带附件目录。

## Verification

- `python3 -m unittest discover -s tests`：9 tests passed。
- Python 编译、`git diff --check`、生成 Gantt JavaScript 语法与关键契约检查通过。
- 浏览器验证任务与事件底部资料栏、桌面/移动布局和无横向溢出。
- 隔离浏览器实例验证图片自然尺寸 `895x994`，点击后成功在全屏遮罩内放大显示。
- 主服务已重启，`http://127.0.0.1:8091/gantt.html` 返回 200。

## Data Safety

已有 `portable/gantt/latest` 快照改动没有进入功能提交；代码提交仅包含实现和测试，避免混入用户数据快照。
