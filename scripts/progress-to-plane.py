#!/usr/bin/env python3
"""Turn a progress sentence into a preview or confirmed Plane API updates."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from progress_lib import build_progress_result, format_preview, utc_now, write_audit


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMELINE = ROOT_DIR / "exports/plane/timeline.jsonl"
DEFAULT_AUDIT_DIR = ROOT_DIR / "exports/progress"


def source_id_from_time() -> str:
    return "manual-" + utc_now().replace("+00:00", "Z").replace(":", "").replace("-", "")


def run_export(timeline_path: Path) -> None:
    subprocess.run(
        [
            str(ROOT_DIR / "scripts/export-plane-timeline.sh"),
            "--since",
            "1970-01-01T00:00:00Z",
            "--output",
            str(timeline_path),
        ],
        cwd=ROOT_DIR,
        check=True,
    )


def apply_changes(result: dict, dry_run: bool) -> int:
    if dry_run:
        result["skipped_changes"].append({"reason": "dry_run", "count": len(result["planned_plane_changes"])})
        return 0

    if not os.environ.get("PLANE_API_KEY"):
        result["auth_gate"] = {
            "status": "blocked",
            "reason": "PLANE_API_KEY is required for --apply",
            "next_step": "Create a Plane API key, export it as PLANE_API_KEY, then re-run with --apply.",
        }
        return 2

    exit_code = 0
    for change in result["planned_plane_changes"]:
        if change.get("operation") != "plane_api_comment" or change.get("mode") != "apply_ready":
            result["skipped_changes"].append(
                {
                    "change_id": change.get("change_id"),
                    "reason": change.get("reason", "not apply-ready"),
                    "operation": change.get("operation"),
                }
            )
            continue

        target = change["target"]
        command = [
            str(ROOT_DIR / "scripts/plane-api-comment.py"),
            "--workspace",
            str(target["workspace_slug"]),
            "--project-id",
            str(target["project_id"]),
            "--issue-id",
            str(target["issue_id"]),
            "--comment",
            str(change["body"]),
            "--external-id",
            str(change["external_id"]),
            "--apply",
        ]
        completed = subprocess.run(command, cwd=ROOT_DIR, text=True, capture_output=True)
        result["applied_changes"].append(
            {
                "change_id": change["change_id"],
                "returncode": completed.returncode,
                "stdout": completed.stdout[:2000],
                "stderr": completed.stderr[:2000],
            }
        )
        if completed.returncode != 0:
            exit_code = completed.returncode
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or apply conversational progress updates to Plane.")
    parser.add_argument("text", nargs="?", help="Progress text. Reads stdin when omitted.")
    parser.add_argument("--source-id", help="Stable source id for traceability.")
    parser.add_argument("--timeline", default=str(DEFAULT_TIMELINE), help="Timeline JSONL path.")
    parser.add_argument("--audit-dir", default=str(DEFAULT_AUDIT_DIR), help="Audit output directory.")
    parser.add_argument("--refresh-timeline", action="store_true", help="Run export-plane-timeline.sh before resolving.")
    parser.add_argument("--apply", action="store_true", help="Apply resolved comments through Plane API. Requires PLANE_API_KEY.")
    parser.add_argument("--json", action="store_true", help="Print JSON result instead of human preview.")
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    text = text.strip()
    if not text:
        print("No progress text provided.", file=sys.stderr)
        return 2

    timeline_path = Path(args.timeline)
    if not timeline_path.is_absolute():
        timeline_path = ROOT_DIR / timeline_path
    if args.refresh_timeline or not timeline_path.exists():
        run_export(timeline_path)

    source_id = args.source_id or source_id_from_time()
    result = build_progress_result(text, source_id, timeline_path, mode="apply" if args.apply else "dry_run")
    apply_exit = apply_changes(result, dry_run=not args.apply)
    audit_path = write_audit(result, args.audit_dir)
    result["audit_path"] = str(audit_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_preview(result))
        print()
        print(f"Audit: {audit_path}")
        if result.get("auth_gate"):
            print(f"Auth gate: {result['auth_gate']['next_step']}", file=sys.stderr)
    return apply_exit


if __name__ == "__main__":
    raise SystemExit(main())
