#!/usr/bin/env python3
"""Export a commit-friendly portable Gantt snapshot."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DELIVERY_DIR = ROOT_DIR / "exports/delivery"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "portable/gantt/latest"
PORTABLE_SCHEMA = "plane-demand-hub.gantt-portable.v1"
EDIT_SCHEMA = "plane-demand-hub.gantt-edits.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def baseline_changeset(gantt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": EDIT_SCHEMA,
        "generated_at": utc_now(),
        "source_gantt_generated_at": gantt.get("generated_at"),
        "note": "Portable baseline snapshot generated without local edit changeset.",
        "new_tasks": [],
        "task_changes": [],
        "event_changes": [],
        "new_events": [],
        "deleted_tasks": [],
        "deleted_events": [],
        "snapshot": {
            "tasks": gantt.get("tasks", []),
            "events": gantt.get("events", []),
        },
    }


def ensure_snapshot(changeset: dict[str, Any], gantt: dict[str, Any]) -> dict[str, Any]:
    snapshot = changeset.get("snapshot")
    if isinstance(snapshot, dict) and isinstance(snapshot.get("tasks"), list) and isinstance(snapshot.get("events"), list):
        return changeset
    next_changeset = dict(changeset)
    next_changeset["snapshot"] = {
        "tasks": gantt.get("tasks", []),
        "events": gantt.get("events", []),
    }
    return next_changeset


def read_changeset(delivery_dir: Path, changeset_path: Path | None, gantt: dict[str, Any]) -> dict[str, Any]:
    source = changeset_path or delivery_dir / "gantt-local-edits.json"
    if source.exists():
        return ensure_snapshot(read_json(source), gantt)
    return baseline_changeset(gantt)


def windows_bat() -> str:
    return """@echo off
setlocal
cd /d "%~dp0\\..\\..\\.."
echo Starting Plane Demand Hub Gantt at http://127.0.0.1:8091/gantt.html
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
) else (
  python scripts\\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
)
pause
"""


def windows_ps1() -> str:
    return """$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\\..\\..")
Set-Location $Root
Write-Host "Starting Plane Demand Hub Gantt at http://127.0.0.1:8091/gantt.html"
if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 scripts\\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
} else {
  & python scripts\\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
}
"""


def mac_linux_sh() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
echo "Starting Plane Demand Hub Gantt at http://127.0.0.1:8091/gantt.html"
python3 scripts/serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
"""


def readme_text(manifest: dict[str, Any]) -> str:
    exported_at = manifest.get("exported_at", "")
    task_count = manifest.get("counts", {}).get("tasks", 0)
    event_count = manifest.get("counts", {}).get("events", 0)
    return f"""# Portable Gantt Snapshot

This directory is safe to commit. It captures the current Plane Demand Hub Gantt state for another machine.

Exported at: `{exported_at}`

Snapshot contents:

- `gantt.html`: portable Gantt page
- `gantt.json`: generated base Gantt data
- `gantt-local-edits.json`: current local edits plus full task/event snapshot
- `manifest.json`: export metadata
- `start-windows.bat` / `start-windows.ps1`: Windows launch helpers

Counts:

- Tasks: {task_count}
- Events: {event_count}

## Windows Quick Start

1. Clone the repository.
2. Double-click `portable\\gantt\\latest\\start-windows.bat`.
3. Open `http://127.0.0.1:8091/gantt.html`.

If double-click is blocked by policy, open PowerShell at the repository root and run:

```powershell
py -3 scripts\\serve-delivery-dashboard.py --port 8091
```

## Updating This Snapshot

From the repository root:

```bash
python3 scripts/export-gantt-portable.py
git add portable/gantt/latest
git commit -m "data: update portable gantt snapshot"
git push
```

The Gantt page also has a `导出迁移快照` button that writes this same directory when served through `scripts/serve-delivery-dashboard.py`.

## Daily GitHub Backup

Use the backup wrapper to choose the newest browser autosave or pushed changeset, regenerate this directory, commit it, and push it to GitHub:

```bash
python3 scripts/backup-gantt-portable.py --branch codex/phase-06-gantt
```

See `docs/GANTT-PORTABLE-BACKUP.md` for the scheduled midnight backup details.
"""


def export_portable(
    delivery_dir: Path | str = DEFAULT_DELIVERY_DIR,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    changeset: dict[str, Any] | None = None,
    changeset_path: Path | str | None = None,
) -> dict[str, Any]:
    delivery = Path(delivery_dir)
    if not delivery.is_absolute():
        delivery = ROOT_DIR / delivery
    output = Path(output_dir)
    if not output.is_absolute():
        output = ROOT_DIR / output
    changeset_file = Path(changeset_path) if changeset_path else None
    if changeset_file and not changeset_file.is_absolute():
        changeset_file = ROOT_DIR / changeset_file

    gantt_json_path = delivery / "gantt.json"
    gantt_html_path = delivery / "gantt.html"
    if not gantt_json_path.exists():
        raise FileNotFoundError(f"Missing {gantt_json_path}")
    if not gantt_html_path.exists():
        raise FileNotFoundError(f"Missing {gantt_html_path}")

    gantt = read_json(gantt_json_path)
    portable_changeset = ensure_snapshot(changeset or read_changeset(delivery, changeset_file, gantt), gantt)
    snapshot = portable_changeset.get("snapshot") or {}
    exported_at = utc_now()

    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gantt_json_path, output / "gantt.json")
    shutil.copy2(gantt_html_path, output / "gantt.html")
    write_json(output / "gantt-local-edits.json", portable_changeset)

    manifest = {
        "schema": PORTABLE_SCHEMA,
        "exported_at": exported_at,
        "source_delivery_dir": display_path(delivery),
        "source_gantt_generated_at": gantt.get("generated_at"),
        "changeset_generated_at": portable_changeset.get("generated_at"),
        "files": [
            "gantt.html",
            "gantt.json",
            "gantt-local-edits.json",
            "manifest.json",
            "README.md",
            "start-windows.bat",
            "start-windows.ps1",
            "start-macos-linux.sh",
        ],
        "counts": {
            "tasks": len(snapshot.get("tasks") or gantt.get("tasks") or []),
            "events": len(snapshot.get("events") or gantt.get("events") or []),
            "new_tasks": len(portable_changeset.get("new_tasks") or []),
            "new_events": len(portable_changeset.get("new_events") or []),
            "task_changes": len(portable_changeset.get("task_changes") or []),
            "event_changes": len(portable_changeset.get("event_changes") or []),
            "deleted_tasks": len(portable_changeset.get("deleted_tasks") or []),
            "deleted_events": len(portable_changeset.get("deleted_events") or []),
        },
    }
    write_json(output / "manifest.json", manifest)
    (output / "README.md").write_text(readme_text(manifest), encoding="utf-8")
    (output / "start-windows.bat").write_text(windows_bat(), encoding="utf-8")
    (output / "start-windows.ps1").write_text(windows_ps1(), encoding="utf-8")
    start_sh = output / "start-macos-linux.sh"
    start_sh.write_text(mac_linux_sh(), encoding="utf-8")
    start_sh.chmod(start_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return {
        "ok": True,
        "directory": display_path(output),
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a portable Gantt snapshot for Git backup and migration.")
    parser.add_argument("--delivery-dir", default=str(DEFAULT_DELIVERY_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--changeset", default=None, help="Optional path to a gantt-local-edits JSON file.")
    args = parser.parse_args()
    result = export_portable(args.delivery_dir, args.output_dir, changeset_path=args.changeset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
