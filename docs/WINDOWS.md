# Windows Guide

Delivery Gantt 可直接在 Windows 10/11 上运行，不需要 Docker 或第三方 Python 包。

## 前置条件

- Python 3.9 或更高版本，并加入 PATH
- Git（仅克隆和备份时需要）

## 启动甘特图

在文件资源管理器中双击：

```text
portable\gantt\latest\start-windows.bat
```

或在 PowerShell 中运行：

```powershell
python scripts\serve-delivery-dashboard.py --host 127.0.0.1 --port 8090
```

然后打开 [http://127.0.0.1:8090/gantt.html](http://127.0.0.1:8090/gantt.html)。

桌面启动器会把可变数据放在 `%APPDATA%\Delivery Gantt`：

```powershell
python scripts\gantt_app.py
```

## 便携导出与备份

```powershell
python scripts\export-gantt-portable.py
python scripts\backup-gantt-portable.py --dry-run --branch codex/phase-06-gantt
```

只有在确实要提交并推送便携快照时，才移除 `--dry-run`。
