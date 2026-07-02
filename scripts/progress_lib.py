#!/usr/bin/env python3
"""Shared progress parsing and Plane resolution helpers."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WAITING_RE = re.compile(r"(排队|等待|卡住|阻塞|blocked|waiting)(?P<duration>[0-9一二三四五六七八九十半两]+天|一天|半天|[0-9]+小时)?", re.I)
DONE_RE = re.compile(r"(完成|已完成|done|finished)", re.I)
IN_PROGRESS_RE = re.compile(r"(开发|推进|处理|调试|实现|优化|进行)", re.I)
ASCII_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        return "waiting", waiting.group(0)
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
    else:
        aliases.append(f"{project}项目")
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


def parse_update(text: str, source_id: str, event_time: str | None = None) -> dict[str, Any]:
    event_time = event_time or utc_now()
    events = []
    planned_changes = []
    warnings = []

    for index, segment in enumerate(split_segments(text), start=1):
        person, project, work_text = split_fields(segment)
        status, blocker = infer_status(work_text)
        work_item = extract_work_item(work_text, status, blocker)

        event = {
            "event_id": f"{source_id}:segment:{index}",
            "event_time": event_time,
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

        body = comment_body(event, work_text)
        planned_changes.append(
            {
                "change_id": f"{source_id}:change:{index}:comment",
                "mode": "dry_run",
                "operation": "add_issue_comment_or_project_note",
                "target": {
                    "project_name": project,
                    "project_aliases": project_aliases(project),
                    "issue_lookup": {"title_contains": work_item},
                },
                "body": body,
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
                        "issue_lookup": {"title_contains": work_item},
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


def comment_body(event: dict[str, Any], work_text: str | None = None) -> str:
    person = event.get("person") or "未指定人员"
    if work_text is None:
        work_item = event.get("work_item") or event.get("raw_text") or ""
        if event.get("status") == "in_progress":
            work_text = f"开发{work_item}"
        else:
            work_text = work_item
    bits = [f"{person}：{work_text}"]
    if event.get("blocker"):
        bits.append(f"阻塞/等待：{event['blocker']}")
    return "；".join(bits)


def load_timeline(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    timeline_path = Path(path)
    if not timeline_path.exists():
        return rows
    for line in timeline_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", "", text).strip().lower()


def ascii_tokens(value: Any) -> set[str]:
    return {token.lower() for token in ASCII_TOKEN_RE.findall(str(value or ""))}


def build_project_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projects: dict[str, dict[str, Any]] = {}
    for row in rows:
        project_id = row.get("project_id")
        if not project_id or project_id in projects:
            continue
        name = row.get("project")
        aliases = project_aliases(name)
        projects[project_id] = {
            "project_id": project_id,
            "project": name,
            "project_aliases": aliases,
            "workspace_slug": row.get("workspace_slug"),
            "workspace": row.get("workspace"),
            "workspace_id": row.get("workspace_id"),
        }
    return list(projects.values())


def resolve_project(event: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    requested_aliases = {normalize_text(alias) for alias in event.get("project_aliases", []) if alias}
    matches = []
    for project in build_project_candidates(rows):
        aliases = {normalize_text(alias) for alias in project.get("project_aliases", []) if alias}
        if requested_aliases & aliases:
            matches.append(project)
    if len(matches) == 1:
        return {"status": "resolved", "project": matches[0], "candidates": matches}
    if len(matches) > 1:
        return {"status": "ambiguous", "project": None, "candidates": matches}
    return {"status": "unresolved", "project": None, "candidates": []}


def issue_score(query: str, row: dict[str, Any]) -> int:
    query_norm = normalize_text(query)
    title_norm = normalize_text(row.get("issue_title"))
    key_norm = normalize_text(row.get("issue_key"))
    if not query_norm:
        return 0
    if query_norm == key_norm:
        return 120
    if query_norm == title_norm:
        return 100
    if query_norm in title_norm or title_norm in query_norm:
        return 80
    overlap = ascii_tokens(query) & ascii_tokens(row.get("issue_title"))
    if overlap:
        return 60 + min(len(overlap) * 5, 20)
    return 0


def resolve_issue(event: dict[str, Any], rows: list[dict[str, Any]], project_id: str | None) -> dict[str, Any]:
    if not project_id:
        return {"status": "unresolved", "issue": None, "candidates": []}
    issue_rows = [row for row in rows if row.get("project_id") == project_id and row.get("issue_id")]
    by_issue: dict[str, dict[str, Any]] = {}
    for row in issue_rows:
        by_issue.setdefault(row["issue_id"], row)

    scored = []
    for row in by_issue.values():
        score = issue_score(event.get("work_item") or "", row)
        if score > 0:
            scored.append((score, row))
    if not scored:
        return {"status": "unresolved", "issue": None, "candidates": []}

    scored.sort(key=lambda item: (-item[0], normalize_text(item[1].get("issue_title"))))
    best_score = scored[0][0]
    best = [row for score, row in scored if score == best_score]
    candidates = [{"score": score, "issue": issue_ref(row)} for score, row in scored[:5]]
    if best_score >= 60 and len(best) == 1:
        return {"status": "resolved", "issue": issue_ref(best[0]), "score": best_score, "candidates": candidates}
    return {"status": "ambiguous", "issue": None, "score": best_score, "candidates": candidates}


def issue_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "workspace_slug": row.get("workspace_slug"),
        "workspace": row.get("workspace"),
        "workspace_id": row.get("workspace_id"),
        "project_id": row.get("project_id"),
        "project": row.get("project"),
        "issue_id": row.get("issue_id"),
        "issue_key": row.get("issue_key"),
        "issue_title": row.get("issue_title"),
    }


def resolve_events(parsed: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    events = []
    planned_changes = []
    warnings = list(parsed.get("warnings", []))

    for event in parsed.get("events", []):
        event = dict(event)
        project_resolution = resolve_project(event, rows)
        project = project_resolution.get("project")
        issue_resolution = resolve_issue(event, rows, project.get("project_id") if project else None)
        event["resolution"] = {
            "project": project_resolution,
            "issue": issue_resolution,
        }
        events.append(event)

        if project_resolution["status"] != "resolved":
            warnings.append(f"{event['event_id']}: project {project_resolution['status']}")
        if issue_resolution["status"] != "resolved":
            warnings.append(f"{event['event_id']}: issue {issue_resolution['status']}")

        change_id = f"{event['source']['source_id']}:change:{event['source']['segment_index']}:comment"
        body = comment_body(event)
        if issue_resolution["status"] == "resolved":
            issue = issue_resolution["issue"]
            planned_changes.append(
                {
                    "change_id": change_id,
                    "mode": "apply_ready",
                    "operation": "plane_api_comment",
                    "target": issue,
                    "body": body,
                    "external_id": event["event_id"],
                    "source_event_id": event["event_id"],
                }
            )
        else:
            planned_changes.append(
                {
                    "change_id": change_id,
                    "mode": "draft",
                    "operation": "manual_target_required",
                    "target": {
                        "project_resolution": project_resolution,
                        "issue_resolution": issue_resolution,
                    },
                    "body": body,
                    "reason": f"issue {issue_resolution['status']}",
                    "source_event_id": event["event_id"],
                }
            )

    return {
        "events": events,
        "planned_plane_changes": planned_changes,
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_progress_result(
    text: str,
    source_id: str,
    timeline_path: str | Path,
    mode: str = "dry_run",
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    parsed = parse_update(text, source_id, event_time=generated_at)
    rows = load_timeline(timeline_path)
    resolved = resolve_events(parsed, rows)
    return {
        "mode": mode,
        "source_id": source_id,
        "generated_at": generated_at,
        "input": text,
        "timeline_path": str(timeline_path),
        "timeline_rows": len(rows),
        "events": resolved["events"],
        "planned_plane_changes": resolved["planned_plane_changes"],
        "warnings": resolved["warnings"],
        "applied_changes": [],
        "skipped_changes": [],
        "write_boundary": "Apply only through Plane API with explicit --apply and PLANE_API_KEY; never write Plane PostgreSQL directly.",
    }


def format_preview(result: dict[str, Any]) -> str:
    lines = [
        "Progress preview",
        f"  mode: {result['mode']}",
        f"  source_id: {result['source_id']}",
        f"  timeline_rows: {result['timeline_rows']}",
        "",
        "Events:",
    ]
    for event in result.get("events", []):
        issue = event.get("resolution", {}).get("issue", {})
        issue_status = issue.get("status")
        issue_ref_text = "unresolved"
        if issue_status == "resolved":
            target = issue.get("issue", {})
            issue_ref_text = f"{target.get('issue_key')} {target.get('issue_title')}"
        lines.append(
            f"  - {event.get('person')}: {event.get('project')} / {event.get('work_item')} "
            f"[{event.get('status')}; issue={issue_ref_text}]"
        )
        if event.get("blocker"):
            lines.append(f"    blocker: {event['blocker']}")
    lines.append("")
    lines.append("Planned changes:")
    for change in result.get("planned_plane_changes", []):
        target = change.get("target", {})
        if change.get("operation") == "plane_api_comment":
            target_text = f"{target.get('issue_key')} {target.get('issue_title')}"
        else:
            target_text = change.get("reason", "manual target required")
        lines.append(f"  - {change['mode']} {change['operation']}: {target_text}")
        lines.append(f"    {change['body']}")
    if result.get("warnings"):
        lines.append("")
        lines.append("Warnings:")
        for warning in result["warnings"]:
            lines.append(f"  - {warning}")
    return "\n".join(lines)


def write_audit(result: dict[str, Any], audit_dir: str | Path) -> Path:
    out_dir = Path(audit_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", result["source_id"])
    out_path = out_dir / f"{safe_id}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return out_path
