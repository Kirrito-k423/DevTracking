# Plane Demand Hub

Plane Demand Hub 是一个围绕自托管 [Plane](https://plane.so/) 构建的本地优先交付协作系统。它把自然语言每日进展转换为可确认的 Plane 变更、时间线、交付看板、报告和可编辑甘特图，同时保持 Plane 为任务与项目管理界面。

## 架构与设计

- [交互式架构图](docs/architecture/plane-demand-hub-architecture.html) — 使用 Archify 生成，支持深浅主题以及 PNG、JPEG、WebP、SVG 导出；克隆仓库后可直接用浏览器打开。
- [架构与设计文档](docs/ARCHITECTURE.md) — 运行模式、组件模型、数据流、信任边界、数据契约和关键设计决策。
- [Archify JSON IR](docs/architecture/plane-demand-hub.architecture.json) — 可验证、可重新渲染的架构图源文件。

## Windows 使用

如果只使用已发布的桌面甘特图，**不需要安装 Docker**。从 [GitHub Releases](https://github.com/Kirrito-k423/DevTracking/releases) 下载 Windows ZIP，解压后运行其中的可执行文件即可。桌面程序会在本机启动轻量 HTTP 服务并打开浏览器。

Docker 仅用于运行可选的完整 Plane 自托管服务；源代码模式的甘特图边车同样可以直接通过 Python 运行。

详细说明：

- [Windows 运行指南](docs/WINDOWS.md)
- [桌面版构建与发布](docs/GANTT-DESKTOP-RELEASE.md)
- [便携快照与备份](docs/GANTT-PORTABLE-BACKUP.md)
- [Plane 快速开始](docs/PLANE-QUICKSTART.md)

## 核心数据边界

- Plane PostgreSQL 仅用于只读分析与时间线抽取。
- 常规 Plane 写入必须通过 API，并由 `--apply` 与 `PLANE_API_KEY` 显式授权。
- 甘特图可变状态、自动保存和便携快照独立于 Plane 内部数据库结构。
- 本地服务默认只监听 `127.0.0.1`。

## 主要目录

| 路径 | 用途 |
|---|---|
| `scripts/` | 时间线抽取、进度解析、报告、甘特图生成与本地服务 |
| `exports/` | 生成的交付看板、报告和运行时快照 |
| `portable/gantt/latest/` | 可克隆、可迁移的甘特图快照 |
| `docs/` | 使用说明、架构设计与运行指南 |
| `.github/workflows/` | Windows/macOS 桌面版构建与 Release 发布 |

## 安全说明

不要提交 `plane.env`、API Token、生成的 Secret、远程服务器密码或个人联系及支付标识。
