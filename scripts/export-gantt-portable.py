#!/usr/bin/env python3
"""Export a commit-friendly portable Gantt snapshot."""

from __future__ import annotations

import argparse
import json
import re
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
ATTACHMENT_DIRECTORY = "gantt-attachments"
ATTACHMENT_EXTENSIONS = {
    ".zip", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
    ".txt", ".ppt", ".pptx", ".doc", ".docx",
}


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
            "attachments": [],
        },
    }


def ensure_snapshot(changeset: dict[str, Any], gantt: dict[str, Any]) -> dict[str, Any]:
    snapshot = changeset.get("snapshot")
    if isinstance(snapshot, dict) and isinstance(snapshot.get("tasks"), list) and isinstance(snapshot.get("events"), list):
        next_changeset = dict(changeset)
        next_snapshot = dict(snapshot)
        if not isinstance(next_snapshot.get("attachments"), list):
            next_snapshot["attachments"] = []
        next_changeset["snapshot"] = next_snapshot
        return next_changeset
    next_changeset = dict(changeset)
    next_changeset["snapshot"] = {
        "tasks": gantt.get("tasks", []),
        "events": gantt.get("events", []),
        "attachments": [],
    }
    return next_changeset


def attachment_storage_name(value: Any) -> str | None:
    name = str(value or "")
    if not name or Path(name).name != name:
        return None
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}\.[A-Za-z0-9]{1,8}", name):
        return None
    if Path(name).suffix.lower() not in ATTACHMENT_EXTENSIONS:
        return None
    return name


def export_attachments(delivery: Path, output: Path, attachments: list[dict[str, Any]]) -> tuple[list[str], int]:
    source_dir = delivery / ATTACHMENT_DIRECTORY
    target_dir = output / ATTACHMENT_DIRECTORY
    seen: set[str] = set()
    ordered_names: list[str] = []
    for attachment in attachments:
        name = attachment_storage_name(attachment.get("storage_name"))
        if not name:
            raise ValueError(f"Invalid attachment storage name: {attachment.get('storage_name')}")
        if name in seen:
            raise ValueError(f"Duplicate attachment storage name: {name}")
        seen.add(name)
        ordered_names.append(name)
    if source_dir.resolve() == target_dir.resolve():
        names = ordered_names
        missing = [name for name in names if not (source_dir / name).is_file()]
        if missing:
            raise FileNotFoundError(f"Missing attachment files: {', '.join(missing)}")
        return [f"{ATTACHMENT_DIRECTORY}/{name}" for name in names], sum((source_dir / name).stat().st_size for name in names)

    if target_dir.exists():
        shutil.rmtree(target_dir)
    exported: list[str] = []
    total_bytes = 0
    for attachment in attachments:
        name = attachment_storage_name(attachment.get("storage_name"))
        assert name is not None
        source = source_dir / name
        if not source.is_file():
            raise FileNotFoundError(f"Missing attachment file: {source}")
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target_dir / name)
        exported.append(f"{ATTACHMENT_DIRECTORY}/{name}")
        total_bytes += source.stat().st_size
    return exported, total_bytes


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
if not errorlevel 1 (
  py -3 scripts\\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    python scripts\\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
  ) else (
    echo Python 3 was not found. Install it from https://www.python.org/downloads/windows/ and enable "Add python.exe to PATH".
  )
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
  $Python = Get-Command python -ErrorAction SilentlyContinue
  if (-not $Python) {
    throw 'Python 3 was not found. Install it from https://www.python.org/downloads/windows/ and enable "Add python.exe to PATH".'
  }
  & $Python.Source scripts\\serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
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
    attachment_count = manifest.get("counts", {}).get("attachments", 0)
    return f"""# Portable Gantt Snapshot

This directory is safe to commit. It captures the current Plane Demand Hub Gantt state for another machine.

Exported at: `{exported_at}`

Snapshot contents:

- `gantt.html`: portable Gantt page
- `gantt.json`: generated base Gantt data
- `gantt-local-edits.json`: current local edits plus full task/event snapshot
- `gantt-attachments/`: files bound to tasks and events
- `manifest.json`: export metadata
- `start-windows.bat` / `start-windows.ps1`: Windows launch helpers

Counts:

- Tasks: {task_count}
- Events: {event_count}
- Attachments: {attachment_count}

## Windows Quick Start

1. Clone the repository.
2. Double-click `portable\\gantt\\latest\\start-windows.bat`.
3. Open `http://127.0.0.1:8091/gantt.html`.

If double-click is blocked by policy, open PowerShell at the repository root and run:

```powershell
python scripts\\serve-delivery-dashboard.py --port 8091
```

## Updating This Snapshot

From the repository root:

```powershell
python scripts\\export-gantt-portable.py
git add portable/gantt/latest
git commit -m "data: update portable gantt snapshot"
git push
```

The Gantt page also has `导出` and `导入` migration package buttons when served through `scripts/serve-delivery-dashboard.py`.

## Daily GitHub Backup

Use the backup wrapper to choose the newest browser autosave or pushed changeset, regenerate this directory, commit it, and push it to GitHub:

```powershell
python scripts\\backup-gantt-portable.py --branch codex/phase-06-gantt
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
    attachments = snapshot.get("attachments") or []
    exported_at = utc_now()

    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gantt_json_path, output / "gantt.json")
    shutil.copy2(gantt_html_path, output / "gantt.html")
    write_json(output / "gantt-local-edits.json", portable_changeset)
    attachment_files, attachment_bytes = export_attachments(delivery, output, attachments)

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
        ] + attachment_files,
        "counts": {
            "tasks": len(snapshot.get("tasks") or gantt.get("tasks") or []),
            "events": len(snapshot.get("events") or gantt.get("events") or []),
            "attachments": len(attachments),
            "attachment_bytes": attachment_bytes,
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
