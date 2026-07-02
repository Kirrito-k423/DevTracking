#!/usr/bin/env python3
"""Generate delivery reports, AI context, and backup manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def source_ref(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    if source.get("source_id"):
        return f"source:{source.get('source_id')}#{source.get('segment_index')}"
    if source.get("table"):
        return f"plane:{source.get('table')}:{source.get('id')}"
    return "source:unknown"


def daily_report(data: dict[str, Any], generated_at: str) -> str:
    lines = ["# Daily Delivery Report", "", f"Generated: {generated_at}", ""]
    summary = data["summary"]
    lines.extend(
        [
            "## Snapshot",
            "",
            f"- Projects: {summary['projects']}",
            f"- Work items: {summary['issues']}",
            f"- People with progress evidence: {summary['people']}",
            f"- Active blockers: {summary['blockers']}",
            f"- Unresolved drafts: {summary['unresolved_drafts']}",
            "",
            "## Progress Evidence",
            "",
        ]
    )
    for person in data.get("people", []):
        work = ", ".join(item.get("work_item") or "" for item in person.get("work_items", []))
        lines.append(f"- {person['person']}: {work or 'no work item text'}")
    lines.extend(["", "## Blockers", ""])
    if data.get("blockers"):
        for blocker in data["blockers"]:
            lines.append(
                f"- {blocker.get('person')} / {blocker.get('project')} / {blocker.get('work_item')}: {blocker.get('blocker')} ({source_ref(blocker)})"
            )
    else:
        lines.append("- None detected")
    lines.extend(["", "## Unresolved Drafts", ""])
    for item in data.get("unresolved_drafts", []):
        lines.append(f"- {item.get('body')} - next: {item.get('next_action')} ({item.get('source_event_id')})")
    if not data.get("unresolved_drafts"):
        lines.append("- None")
    return "\n".join(lines) + "\n"


def weekly_report(data: dict[str, Any], generated_at: str) -> str:
    lines = ["# Weekly Delivery Report", "", f"Generated: {generated_at}", ""]
    for project in data.get("projects", []):
        lines.extend([f"## {project['project']}", ""])
        lines.append(f"- State counts: {project.get('state_counts')}")
        lines.append(f"- People: {', '.join(project.get('people', {}).keys()) or 'unknown'}")
        lines.append(f"- Blockers: {len(project.get('blockers', []))}")
        lines.append(f"- Unresolved drafts: {len(project.get('unresolved', []))}")
        lines.append(f"- Next review: {project.get('next_review_date')}")
        lines.append("")
        lines.append("### Work Items")
        for issue in project.get("issues", []):
            lines.append(f"- {issue.get('issue_key')} {issue.get('issue_title')} [{issue.get('state') or 'unknown'}]")
        if not project.get("issues"):
            lines.append("- None in source window")
        lines.append("")
    return "\n".join(lines) + "\n"


def risk_help_report(data: dict[str, Any], generated_at: str) -> str:
    lines = ["# Risk And Help Report", "", f"Generated: {generated_at}", ""]
    lines.append("## Help Needed")
    lines.append("")
    if data.get("blockers"):
        for blocker in data["blockers"]:
            lines.append(f"- Owner: {blocker.get('person')}")
            lines.append(f"  Project: {blocker.get('project')}")
            lines.append(f"  Work: {blocker.get('work_item')}")
            lines.append(f"  Blocker: {blocker.get('blocker')}")
            lines.append("  Needed help: confirm queue/resource owner and expected unblock time")
            lines.append(f"  Source: {source_ref(blocker)}")
    else:
        lines.append("- No active blockers detected")
    lines.extend(["", "## Unresolved Draft Risks", ""])
    for item in data.get("unresolved_drafts", []):
        lines.append(f"- {item.get('body')} ({item.get('reason')}); next: {item.get('next_action')}")
    if not data.get("unresolved_drafts"):
        lines.append("- None")
    return "\n".join(lines) + "\n"


def retrospective_report(data: dict[str, Any], generated_at: str) -> str:
    lines = ["# Project Retrospective", "", f"Generated: {generated_at}", ""]
    lines.extend(["## Key Nodes", ""])
    for row in data.get("timeline", []):
        lines.append(f"- {row.get('event_time')} {row.get('project')} {row.get('issue_key')} {row.get('event_type')} ({source_ref(row)})")
    lines.extend(["", "## Blockers And Breakthroughs", ""])
    if data.get("blockers"):
        for blocker in data["blockers"]:
            lines.append(f"- Blocker: {blocker.get('person')} / {blocker.get('work_item')} / {blocker.get('blocker')}")
    else:
        lines.append("- No blockers detected")
    lines.extend(["", "## Contributors", ""])
    for person in data.get("people", []):
        lines.append(f"- {person['person']}: {person['events']} progress event(s)")
    lines.extend(["", "## Follow-Up Actions", ""])
    for project in data.get("projects", []):
        for action in project.get("next_actions", []):
            lines.append(f"- {project['project']}: {action}")
    return "\n".join(lines) + "\n"


def write_ai_context(data: dict[str, Any], output_dir: Path, generated_at: str) -> Path:
    path = output_dir / "ai-context.jsonl"
    rows = []
    for project in data.get("projects", []):
        rows.append(
            {
                "type": "project_snapshot",
                "generated_at": generated_at,
                "project": project["project"],
                "summary": f"{project['project']} has {len(project.get('issues', []))} issue(s), {len(project.get('blockers', []))} blocker(s), {len(project.get('unresolved', []))} unresolved draft(s).",
                "source": "exports/delivery/dashboard.json",
            }
        )
    for blocker in data.get("blockers", []):
        rows.append(
            {
                "type": "blocker",
                "generated_at": generated_at,
                "project": blocker.get("project"),
                "person": blocker.get("person"),
                "summary": f"{blocker.get('person')} is waiting on {blocker.get('work_item')}: {blocker.get('blocker')}",
                "source": blocker.get("source"),
            }
        )
    for item in data.get("unresolved_drafts", []):
        rows.append(
            {
                "type": "unresolved_draft",
                "generated_at": generated_at,
                "summary": item.get("body"),
                "source_event_id": item.get("source_event_id"),
                "next_action": item.get("next_action"),
            }
        )
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_remotes() -> list[str]:
    completed = subprocess.run(["git", "remote", "-v"], cwd=ROOT_DIR, text=True, capture_output=True)
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def write_manifest(files: list[Path], backup_dir: Path, generated_at: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    remotes = git_remotes()
    manifest = {
        "generated_at": generated_at,
        "remote_available": bool(remotes),
        "git_remotes": remotes,
        "github_backup_status": "ready" if remotes else "remote_missing",
        "files": [
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
            if path.exists()
        ],
        "excluded": [
            "plane-selfhost/plane-app/plane.env",
            "API tokens",
            "generated secrets",
        ],
    }
    path = backup_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate delivery reports and backup manifest.")
    parser.add_argument("--dashboard", default=str(ROOT_DIR / "exports/delivery/dashboard.json"))
    parser.add_argument("--output-dir", default=str(ROOT_DIR / "exports/reports"))
    parser.add_argument("--backup-dir", default=str(ROOT_DIR / "exports/backup"))
    args = parser.parse_args()

    generated_at = now()
    dashboard_path = Path(args.dashboard)
    output_dir = Path(args.output_dir)
    backup_dir = Path(args.backup_dir)
    data = load_json(dashboard_path)

    files = [
        write(output_dir / "daily.md", daily_report(data, generated_at)),
        write(output_dir / "weekly.md", weekly_report(data, generated_at)),
        write(output_dir / "risk-help.md", risk_help_report(data, generated_at)),
        write(output_dir / "retrospective.md", retrospective_report(data, generated_at)),
        write_ai_context(data, output_dir, generated_at),
        dashboard_path,
    ]
    manifest = write_manifest(files, backup_dir, generated_at)
    print(f"Wrote reports to {output_dir}")
    print(f"Wrote backup manifest to {manifest}")
    print(json.dumps({"reports": 5, "remote_available": bool(git_remotes())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

