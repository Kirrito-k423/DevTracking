#!/usr/bin/env python3
"""Parse a small Chinese daily progress update into dry-run Plane changes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone


WAITING_RE = re.compile(r"(排队|等待|卡住|阻塞|blocked|waiting)(?P<duration>[0-9一二三四五六七八九十半两]+天|一天|半天|[0-9]+小时)?", re.I)
DONE_RE = re.compile(r"(完成|已完成|done|finished)", re.I)
IN_PROGRESS_RE = re.compile(r"(开发|推进|处理|调试|实现|优化|进行)", re.I)


def split_segments(text: str) -> list[str]:
    normalized = text.replace("\n", "；")
    return [segment.strip(" ，,。.;；\t") for segment in re.split(r"[；;]+", normalized) if segment.strip()]


def split_fields(segment: str) -> tuple[str | None, str | None, str]:
    fields = [item.strip(" ，,。") for item in re.split(r"[，,]+", segment) if item.strip()]
    if len(fields) >= 3:
      return fields[0], fields[1], "，".join(fields[2:])
    if len(fields) == 2:
      return fields[0], None, fields[1]
    return None, None, segment


def infer_status(work_text: str) -> tuple[str, str | None]:
    waiting = WAITING_RE.search(work_text)
    if waiting:
        blocker = waiting.group(0)
        return "waiting", blocker
    if DONE_RE.search(work_text):
        return "completed", None
    if IN_PROGRESS_RE.search(work_text):
        return "in_progress", None
    return "reported", None


def project_aliases(project: str | None) -> list[str]:
    if not project:
        return []
    aliases = [project]
    if project.endswith("项目") and len(project) > 2:
        aliases.append(project[:-2])
    return list(dict.fromkeys(aliases))


def extract_work_item(work_text: str, status: str, blocker: str | None) -> str:
    cleaned = work_text.strip(" ，,。")
    if blocker:
        cleaned = cleaned.replace(blocker, "").strip(" ，,。")
    for verb in ("正在开发", "开发", "推进", "处理", "调试", "实现", "优化", "完成", "已完成"):
        if cleaned.startswith(verb):
            cleaned = cleaned[len(verb):].strip(" ：:，,。")
            break
    return cleaned or work_text.strip(" ，,。")


def parse_update(text: str, source_id: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    events = []
    planned_changes = []
    warnings = []

    for index, segment in enumerate(split_segments(text), start=1):
        person, project, work_text = split_fields(segment)
        status, blocker = infer_status(work_text)
        work_item = extract_work_item(work_text, status, blocker)

        event = {
            "event_id": f"{source_id}:segment:{index}",
            "event_time": now,
            "person": person,
            "project": project,
            "project_aliases": project_aliases(project),
            "work_item": work_item,
            "status": status,
            "blocker": blocker,
            "raw_text": segment,
            "source": {
                "type": "user_progress_message",
                "source_id": source_id,
                "segment_index": index,
            },
        }
        events.append(event)

        if not person:
            warnings.append(f"segment {index}: missing person")
        if not project:
            warnings.append(f"segment {index}: missing project")

        comment_bits = [f"{person or '未指定人员'}：{work_text}"]
        if blocker:
            comment_bits.append(f"阻塞/等待：{blocker}")

        planned_changes.append(
            {
                "change_id": f"{source_id}:change:{index}:comment",
                "mode": "dry_run",
                "operation": "add_issue_comment_or_project_note",
                "target": {
                    "project_name": project,
                    "project_aliases": project_aliases(project),
                    "issue_lookup": {
                        "title_contains": work_item,
                    },
                },
                "body": "；".join(comment_bits),
                "source_event_id": event["event_id"],
            }
        )

        if status == "waiting":
            planned_changes.append(
                {
                    "change_id": f"{source_id}:change:{index}:blocker",
                    "mode": "dry_run",
                    "operation": "mark_blocker_or_create_follow_up",
                    "target": {
                        "project_name": project,
                        "project_aliases": project_aliases(project),
                        "issue_lookup": {
                            "title_contains": work_item,
                        },
                    },
                    "blocker": blocker,
                    "source_event_id": event["event_id"],
                }
            )

    return {
        "mode": "dry_run",
        "source_id": source_id,
        "input": text,
        "events": events,
        "planned_plane_changes": planned_changes,
        "warnings": warnings,
        "write_boundary": "Preview only. Apply through Plane API/session connector after confirmation; never write Plane PostgreSQL directly.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse daily progress text into dry-run Plane changes.")
    parser.add_argument("text", nargs="?", help="Progress text. Reads stdin when omitted.")
    parser.add_argument("--source-id", default="manual-2026-07-02-001", help="Stable source id for traceability.")
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    text = text.strip()
    if not text:
        print("No progress text provided.", file=sys.stderr)
        return 2

    result = parse_update(text, args.source_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
