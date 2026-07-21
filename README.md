# Delivery Gantt

Delivery Gantt 是一个本地优先、无需 Docker 的可编辑交付甘特图。它使用 Python 标准库启动轻量 HTTP 服务，并把任务、事件、附件、自动保存和迁移快照保存在本地文件中。

## 本机启动

在仓库根目录运行：

```bash
portable/gantt/latest/start-macos-linux.sh
```

然后访问 [http://127.0.0.1:8090/gantt.html](http://127.0.0.1:8090/gantt.html)。

也可以直接运行：

```bash
python3 scripts/serve-delivery-dashboard.py --host 127.0.0.1 --port 8090
```

## Windows 与桌面版

- Windows 双击 `portable\gantt\latest\start-windows.bat`
- 桌面启动器：`python scripts\gantt_app.py`
- [Windows 运行指南](docs/WINDOWS.md)
- [桌面版构建与发布](docs/GANTT-DESKTOP-RELEASE.md)
- [便携快照与备份](docs/GANTT-PORTABLE-BACKUP.md)

## 主要目录

| 路径 | 用途 |
|---|---|
| `scripts/serve-delivery-dashboard.py` | 本地 HTTP 服务、自动保存、附件和导入导出 API |
| `scripts/export-gantt-portable.py` | 生成可提交、可迁移的甘特图快照 |
| `scripts/backup-gantt-portable.py` | 选择最新本地状态并备份便携快照 |
| `portable/gantt/latest/` | 甘特图页面、任务事件数据和跨平台启动脚本 |
| `exports/delivery/` | 本机运行时数据与自动保存（默认不提交） |

## 数据边界

- 服务默认只监听 `127.0.0.1`。
- 不依赖外部项目管理系统、数据库或 Docker。
- `portable/gantt/latest/` 是可迁移快照；`exports/delivery/` 是本机可变运行数据。
- 旧版 schema/localStorage 标识为兼容现有快照而保留，不代表仍依赖旧系统。

不要提交 API Token、生成的 Secret、远程服务器密码或个人联系及支付标识。
