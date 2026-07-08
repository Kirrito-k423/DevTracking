#!/usr/bin/env python3
"""Build a static delivery dashboard from Plane timeline and progress audits."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_progress_audits(progress_dir: Path) -> list[dict[str, Any]]:
    if not progress_dir.exists():
        return []
    latest_by_input: dict[str, tuple[float, dict[str, Any]]] = {}
    for path in progress_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        key = data.get("input") or data.get("source_id") or path.name
        mtime = path.stat().st_mtime
        if key not in latest_by_input or latest_by_input[key][0] < mtime:
            data["_audit_path"] = str(path)
            latest_by_input[key] = (mtime, data)
    return [item[1] for item in latest_by_input.values()]


def issue_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "workspace_slug": row.get("workspace_slug"),
        "project_id": row.get("project_id"),
        "project": row.get("project"),
        "issue_id": row.get("issue_id"),
        "issue_key": row.get("issue_key"),
        "issue_title": row.get("issue_title"),
    }


def build_dashboard(timeline: list[dict[str, Any]], audits: list[dict[str, Any]], stale_days: int) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).date().isoformat()
    issues: dict[str, dict[str, Any]] = {}
    timeline_events = sorted(timeline, key=lambda row: row.get("event_time") or "")

    for row in timeline_events:
        issue_id = row.get("issue_id")
        if not issue_id:
            continue
        issue = issues.setdefault(
            issue_id,
            {
                **issue_ref(row),
                "state": None,
                "priority": None,
                "latest_event_time": None,
                "event_count": 0,
                "source_refs": [],
            },
        )
        issue["event_count"] += 1
        issue["latest_event_time"] = row.get("event_time") or issue.get("latest_event_time")
        payload = row.get("payload") or {}
        if payload.get("state"):
            issue["state"] = payload.get("state")
        if payload.get("priority"):
            issue["priority"] = payload.get("priority")
        source = row.get("source") or {}
        issue["source_refs"].append(
            {
                "event_time": row.get("event_time"),
                "event_type": row.get("event_type"),
                "source": source,
            }
        )

    people: dict[str, dict[str, Any]] = {}
    blockers = []
    unresolved = []
    progress_events = []
    seen_progress_keys = set()

    for audit in audits:
        for event in audit.get("events", []):
            event_key = (
                event.get("person"),
                event.get("project"),
                event.get("work_item"),
                event.get("status"),
                event.get("blocker"),
            )
            if event_key in seen_progress_keys:
                continue
            seen_progress_keys.add(event_key)
            progress_events.append(event)
            person = event.get("person") or "未知"
            person_row = people.setdefault(person, {"person": person, "events": 0, "work_items": [], "blockers": []})
            person_row["events"] += 1
            person_row["work_items"].append(
                {
                    "project": event.get("project"),
                    "work_item": event.get("work_item"),
                    "status": event.get("status"),
                    "source": event.get("source"),
                }
            )
            if event.get("blocker"):
                blocker = {
                    "person": person,
                    "project": event.get("project"),
                    "work_item": event.get("work_item"),
                    "blocker": event.get("blocker"),
                    "source": event.get("source"),
                }
                person_row["blockers"].append(blocker)
                blockers.append(blocker)

        for change in audit.get("planned_plane_changes", []):
            if change.get("mode") == "draft" or change.get("operation") == "manual_target_required":
                unresolved.append(
                    {
                        "body": change.get("body"),
                        "reason": change.get("reason"),
                        "source_event_id": change.get("source_event_id"),
                        "next_action": "选择或创建 Plane work item 后再应用更新",
                    }
                )

    projects: dict[str, dict[str, Any]] = {}
    for issue in issues.values():
        project_name = issue.get("project") or "未知项目"
        project = projects.setdefault(
            project_name,
            {
                "project": project_name,
                "issues": [],
                "state_counts": Counter(),
                "people": Counter(),
                "blockers": [],
                "unresolved": [],
                "stale_issues": [],
                "recent_activity": [],
                "next_review_date": tomorrow,
            },
        )
        project["issues"].append(issue)
        project["state_counts"][issue.get("state") or "unknown"] += 1
        latest_dt = parse_dt(issue.get("latest_event_time"))
        if latest_dt and now - latest_dt > timedelta(days=stale_days):
            project["stale_issues"].append(issue)

    for event in progress_events:
        project_name = resolve_project_name(event, projects)
        project = projects.setdefault(
            project_name,
            {
                "project": project_name,
                "issues": [],
                "state_counts": Counter(),
                "people": Counter(),
                "blockers": [],
                "unresolved": [],
                "stale_issues": [],
                "recent_activity": [],
                "next_review_date": tomorrow,
            },
        )
        if event.get("person"):
            project["people"][event["person"]] += 1
        if event.get("blocker"):
            project["blockers"].append(event)

    for item in unresolved:
        project_name = "未知项目"
        source_event_id = item.get("source_event_id")
        for event in progress_events:
            if event.get("event_id") == source_event_id:
                project_name = resolve_project_name(event, projects)
                break
        projects.setdefault(
            project_name,
            {
                "project": project_name,
                "issues": [],
                "state_counts": Counter(),
                "people": Counter(),
                "blockers": [],
                "unresolved": [],
                "stale_issues": [],
                "recent_activity": [],
                "next_review_date": tomorrow,
            },
        )["unresolved"].append(item)

    for row in timeline_events[-30:]:
        project_name = row.get("project") or "未知项目"
        if project_name in projects:
            projects[project_name]["recent_activity"].append(
                {
                    "event_time": row.get("event_time"),
                    "event_type": row.get("event_type"),
                    "issue_key": row.get("issue_key"),
                    "issue_title": row.get("issue_title"),
                    "source": row.get("source"),
                }
            )

    project_list = []
    for project in projects.values():
        project["state_counts"] = dict(project["state_counts"])
        project["people"] = dict(project["people"])
        project["next_actions"] = next_actions(project)
        project_list.append(project)
    project_list.sort(key=lambda item: item["project"])

    return {
        "generated_at": now.isoformat(),
        "sources": {
            "timeline_rows": len(timeline),
            "progress_audits": len(audits),
        },
        "summary": {
            "projects": len(project_list),
            "issues": len(issues),
            "people": len(people),
            "blockers": len(blockers),
            "unresolved_drafts": len(unresolved),
            "stale_issues": sum(len(project["stale_issues"]) for project in project_list),
        },
        "projects": project_list,
        "people": sorted(people.values(), key=lambda item: item["person"]),
        "blockers": blockers,
        "unresolved_drafts": unresolved,
        "timeline": [
            {
                "event_time": row.get("event_time"),
                "event_type": row.get("event_type"),
                "project": row.get("project"),
                "issue_key": row.get("issue_key"),
                "issue_title": row.get("issue_title"),
                "source": row.get("source"),
            }
            for row in timeline_events[-50:]
        ],
    }


def resolve_project_name(event: dict[str, Any], projects: dict[str, Any]) -> str:
    resolution = event.get("resolution", {}).get("project", {})
    project = resolution.get("project") or {}
    if project.get("project"):
        return project["project"]
    for alias in event.get("project_aliases", []):
        if alias in projects:
            return alias
        if alias.endswith("项目") and alias[:-2] in projects:
            return alias[:-2]
    return event.get("project") or "未知项目"


def next_actions(project: dict[str, Any]) -> list[str]:
    actions = []
    if project["blockers"]:
        actions.append("处理等待/阻塞项，确认需要谁协助以及预计解除时间")
    if project["unresolved"]:
        actions.append("为未绑定进展选择或创建 Plane work item")
    if project["stale_issues"]:
        actions.append("复查长期无更新工作项并补充最新状态")
    if not actions:
        actions.append("按下一评审日期复查项目状态")
    return actions


LEADING_DATE_RE = re.compile(r"^\s*(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{4}\s+Q\d)\s*")


def meaningful_label(value: Any) -> str:
    text = " ".join(str(value or "").split())
    text = LEADING_DATE_RE.sub("", text).strip()
    if "：" in text:
        prefix, rest = text.split("：", 1)
        if rest.strip() and (
            re.search(r"\d", prefix)
            or len(prefix) <= 8
            or prefix.endswith(("需求", "SFT", "chunkmoe"))
        ):
            text = rest.strip()
    elif ": " in text:
        prefix, rest = text.split(": ", 1)
        if rest.strip() and (re.search(r"\d", prefix) or len(prefix) <= 12):
            text = rest.strip()
    return text or "未命名"


def compact_label(value: Any, limit: int = 8) -> str:
    text = meaningful_label(value)
    return text[:limit]


def compact_marker_label(value: Any, limit: int = 8) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def normalize_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    parsed = parse_dt(text)
    if parsed:
        return parsed.date().isoformat()
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    return None


def source_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_time": row.get("event_time"),
        "event_type": row.get("event_type"),
        "source": row.get("source") or {},
    }


def append_unique(items: list[Any], value: Any) -> None:
    if value and value not in items:
        items.append(value)


def current_issue_payload(payload: dict[str, Any]) -> dict[str, Any]:
    current: dict[str, Any] = {}
    nested = payload.get("current_issue")
    if isinstance(nested, dict):
        current.update(nested)
    for key in ("parent_id", "start_date", "target_date", "completed_at", "priority", "state"):
        if key in payload:
            current[key] = payload.get(key)
    return current


def issue_sort_key(task: dict[str, Any]) -> tuple[str, int, str]:
    issue_key = task.get("issue_key") or ""
    try:
        sequence = int(str(issue_key).rsplit("-", 1)[-1])
    except ValueError:
        sequence = 999999
    return (task.get("project") or "", sequence, issue_key)


def completed_state(state: Any) -> bool:
    text = str(state or "").strip().lower()
    return text in {"done", "completed", "complete", "closed", "已完成", "完成"} or "done" in text


def blocked_state(state: Any) -> bool:
    text = str(state or "").strip().lower()
    return any(token in text for token in ("blocked", "waiting", "wait", "stuck", "阻塞", "等待", "卡住"))


def estimate_progress(task: dict[str, Any]) -> int:
    state = task.get("state")
    labels = {str(label).lower() for label in task.get("labels", [])}
    if task.get("completed_at") or completed_state(state):
        return 100
    if "blocked" in labels or "needs-help" in labels or blocked_state(state):
        return 25
    if str(state or "").strip().lower() in {"todo", "backlog", "待办"}:
        return 0
    if state:
        return 50
    return 10


def build_gantt_data(timeline: list[dict[str, Any]], audits: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    tasks: dict[str, dict[str, Any]] = {}
    events: dict[str, dict[str, Any]] = {}
    key_to_id: dict[str, str] = {}
    timeline_events = sorted(timeline, key=lambda row: row.get("event_time") or "")

    def ensure_task(row: dict[str, Any]) -> dict[str, Any] | None:
        issue_id = row.get("issue_id")
        if not issue_id:
            return None
        issue_id = str(issue_id)
        task = tasks.setdefault(
            issue_id,
            {
                "id": issue_id,
                "issue_id": issue_id,
                "issue_key": row.get("issue_key"),
                "title": row.get("issue_title") or row.get("issue_key") or issue_id,
                "compact_label": compact_label(row.get("issue_title") or row.get("issue_key") or issue_id),
                "parent_id": None,
                "children": [],
                "depth": 0,
                "order": 0,
                "project": row.get("project"),
                "state": None,
                "priority": None,
                "progress": 0,
                "owner": None,
                "labels": [],
                "modules": [],
                "start_date": None,
                "target_date": None,
                "completed_at": None,
                "source_refs": [],
                "delivery_summary": {},
                "_parent_key": None,
                "_first_event_date": normalize_date(row.get("event_time")),
                "_latest_event_date": normalize_date(row.get("event_time")),
                "_audit_events": [],
            },
        )
        task["issue_key"] = task.get("issue_key") or row.get("issue_key")
        task["title"] = task.get("title") or row.get("issue_title") or row.get("issue_key") or issue_id
        task["project"] = task.get("project") or row.get("project")
        if task.get("issue_key"):
            key_to_id[str(task["issue_key"])] = issue_id
        event_date = normalize_date(row.get("event_time"))
        if event_date:
            task["_first_event_date"] = min(task.get("_first_event_date") or event_date, event_date)
            task["_latest_event_date"] = max(task.get("_latest_event_date") or event_date, event_date)
        task["source_refs"].append(source_ref(row))
        return task

    def add_event(task: dict[str, Any], event_type: str, row: dict[str, Any], label: str, summary: str) -> None:
        event_date = normalize_date(row.get("event_time")) or task.get("target_date") or task.get("start_date")
        event_id = f"{task['id']}:{event_type}:{event_date}:{(row.get('source') or {}).get('id') or len(events)}"
        events.setdefault(
            event_id,
            {
                "id": event_id,
                "task_id": task["id"],
                "type": event_type,
                "compact_label": compact_marker_label(label),
                "date": event_date,
                "summary": summary,
                "source_refs": [source_ref(row)],
            },
        )

    for row in timeline_events:
        task = ensure_task(row)
        if not task:
            continue
        payload = row.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {}
        current = current_issue_payload(payload)
        for field in ("state", "priority"):
            if current.get(field):
                task[field] = current.get(field)
        if current.get("completed_at"):
            task["completed_at"] = current.get("completed_at")
        if current.get("parent_id"):
            task["parent_id"] = str(current.get("parent_id"))
        if current.get("start_date"):
            task["start_date"] = normalize_date(current.get("start_date"))
        if current.get("target_date"):
            task["target_date"] = normalize_date(current.get("target_date"))

        event_type = row.get("event_type")
        if event_type == "issue_activity":
            field = payload.get("field")
            new_value = payload.get("new_value")
            if field == "parent" and new_value:
                task["_parent_key"] = str(new_value)
            elif field == "start_date":
                task["start_date"] = normalize_date(new_value)
            elif field == "target_date":
                task["target_date"] = normalize_date(new_value)
            elif field == "state" and new_value:
                task["state"] = new_value
        elif event_type == "label_added":
            label = payload.get("label")
            append_unique(task["labels"], label)
            label_text = str(label or "")
            label_lower = label_text.lower()
            if label_lower.startswith("owner:"):
                task["owner"] = label_text.split(":", 1)[1].strip() or task.get("owner")
            if label_lower in {"blocked", "needs-help", "blocker"}:
                add_event(task, "blocked", row, "阻塞" if label_lower == "blocked" else "求助", f"{label_text}: {task['title']}")
            if label_lower == "milestone":
                add_event(task, "milestone", row, "里程碑", f"Milestone: {task['title']}")
        elif event_type == "module_linked":
            append_unique(task["modules"], payload.get("module"))
            task["start_date"] = task.get("start_date") or normalize_date(payload.get("start_date"))
            task["target_date"] = task.get("target_date") or normalize_date(payload.get("target_date"))
        elif event_type == "cycle_linked":
            task["start_date"] = task.get("start_date") or normalize_date(payload.get("start_date"))
            task["target_date"] = task.get("target_date") or normalize_date(payload.get("end_date"))
        elif event_type == "assignee_added":
            task["owner"] = task.get("owner") or payload.get("assignee")
        elif event_type == "issue_completed":
            task["completed_at"] = row.get("event_time") or task.get("completed_at")
            task["state"] = task.get("state") or payload.get("state") or "Done"
            add_event(task, "completed", row, "完成", f"Completed: {task['title']}")

    for task in tasks.values():
        raw_parent = task.get("parent_id") or task.get("_parent_key")
        if raw_parent:
            raw_parent = str(raw_parent)
            parent_id = raw_parent if raw_parent in tasks else key_to_id.get(raw_parent, raw_parent)
            if parent_id != task["id"]:
                task["parent_id"] = parent_id
        if not task.get("start_date"):
            task["start_date"] = task.get("_first_event_date")
        if not task.get("target_date"):
            task["target_date"] = task.get("_latest_event_date") or task.get("start_date")
        if task.get("start_date") and task.get("target_date") and task["target_date"] < task["start_date"]:
            task["target_date"] = task["start_date"]

    for task in tasks.values():
        parent_id = task.get("parent_id")
        if parent_id in tasks:
            append_unique(tasks[parent_id]["children"], task["id"])
        elif parent_id:
            task["parent_id"] = None

    for task in tasks.values():
        if not any(event["task_id"] == task["id"] and event["type"] == "completed" for event in events.values()):
            if task.get("completed_at") or completed_state(task.get("state")):
                add_event(
                    task,
                    "completed",
                    {"event_time": task.get("completed_at") or task.get("_latest_event_date"), "event_type": "state_completed", "source": {"table": "issues", "field": "completed_at", "id": task["id"]}},
                    "完成",
                    f"Completed: {task['title']}",
                )
        if blocked_state(task.get("state")) and not any(event["task_id"] == task["id"] and event["type"] == "blocked" for event in events.values()):
            add_event(
                task,
                "blocked",
                {"event_time": task.get("_latest_event_date"), "event_type": "state_blocked", "source": {"table": "issues", "field": "state", "id": task["id"]}},
                "阻塞",
                f"Blocked state: {task['title']}",
            )

    title_index = [(task_id, str(task.get("title") or "").lower()) for task_id, task in tasks.items()]
    for audit in audits:
        audit_source = {"source_id": audit.get("source_id"), "path": audit.get("_audit_path")}
        for progress_event in audit.get("events", []):
            work_item = str(progress_event.get("work_item") or "").lower()
            if not work_item:
                continue
            matched_id = None
            for task_id, title in title_index:
                if work_item in title or title in work_item:
                    matched_id = task_id
                    break
            if not matched_id:
                continue
            task = tasks[matched_id]
            task["_audit_events"].append(progress_event)
            task["owner"] = task.get("owner") or progress_event.get("person")
            task["delivery_summary"]["next_action"] = progress_event.get("next_action") or task["delivery_summary"].get("next_action")
            if progress_event.get("blocker"):
                task["delivery_summary"]["blocker"] = progress_event.get("blocker")
            task["source_refs"].append(
                {
                    "event_time": progress_event.get("event_time"),
                    "event_type": "progress_audit",
                    "source": audit_source,
                }
            )

    def rollup(task_id: str, visiting: set[str] | None = None) -> tuple[str | None, str | None, int]:
        visiting = visiting or set()
        if task_id in visiting:
            return None, None, estimate_progress(tasks[task_id])
        visiting.add(task_id)
        task = tasks[task_id]
        child_ranges = [rollup(child_id, visiting.copy()) for child_id in task["children"] if child_id in tasks]
        child_starts = [item[0] for item in child_ranges if item[0]]
        child_targets = [item[1] for item in child_ranges if item[1]]
        if child_starts and (not task.get("start_date") or min(child_starts) < task["start_date"]):
            task["start_date"] = min(child_starts)
        if child_targets and (not task.get("target_date") or max(child_targets) > task["target_date"]):
            task["target_date"] = max(child_targets)
        if child_ranges:
            task["progress"] = round(sum(item[2] for item in child_ranges) / len(child_ranges))
        else:
            task["progress"] = estimate_progress(task)
        return task.get("start_date"), task.get("target_date"), task["progress"]

    roots = sorted([task_id for task_id, task in tasks.items() if not task.get("parent_id")], key=lambda task_id: issue_sort_key(tasks[task_id]))
    for root_id in roots:
        rollup(root_id)

    ordered: list[dict[str, Any]] = []

    def visit(task_id: str, depth: int, seen: set[str]) -> None:
        if task_id in seen:
            return
        seen.add(task_id)
        task = tasks[task_id]
        task["depth"] = depth
        task["children"].sort(key=lambda child_id: issue_sort_key(tasks[child_id]))
        ordered.append(task)
        for child_id in task["children"]:
            visit(child_id, depth + 1, seen)

    seen_order: set[str] = set()
    for root_id in roots:
        visit(root_id, 0, seen_order)
    for task_id in sorted(tasks, key=lambda item: issue_sort_key(tasks[item])):
        visit(task_id, 0, seen_order)

    for index, task in enumerate(ordered):
        task["order"] = index
        task["compact_label"] = compact_label(task.get("title") or task.get("issue_key"))
        if not task.get("delivery_summary").get("next_action"):
            if any(event["task_id"] == task["id"] and event["type"] == "blocked" for event in events.values()):
                task["delivery_summary"]["next_action"] = "确认阻塞解除时间和协助人"
            elif task.get("children"):
                task["delivery_summary"]["next_action"] = "展开子任务复查交付路径"
            else:
                task["delivery_summary"]["next_action"] = "按最新 Plane 状态继续跟进"
        task["delivery_summary"].update(
            {
                "title": task.get("title"),
                "issue_key": task.get("issue_key"),
                "owner": task.get("owner"),
                "state": task.get("state"),
                "progress": task.get("progress"),
                "date_range": f"{task.get('start_date') or 'n/a'} - {task.get('target_date') or 'n/a'}",
            }
        )

    public_tasks = []
    for task in ordered:
        public_tasks.append(
            {
                key: task.get(key)
                for key in (
                    "id",
                    "issue_id",
                    "issue_key",
                    "title",
                    "compact_label",
                    "parent_id",
                    "children",
                    "depth",
                    "order",
                    "project",
                    "state",
                    "progress",
                    "owner",
                    "labels",
                    "modules",
                    "start_date",
                    "target_date",
                    "completed_at",
                    "source_refs",
                    "delivery_summary",
                )
            }
        )

    event_list = sorted(events.values(), key=lambda event: (event.get("date") or "", event.get("task_id") or "", event.get("type") or ""))
    return {
        "generated_at": now.isoformat(),
        "sources": {
            "timeline_rows": len(timeline),
            "progress_audits": len(audits),
        },
        "summary": {
            "tasks": len(public_tasks),
            "events": len(event_list),
            "parent_links": sum(1 for task in public_tasks if task.get("parent_id")),
            "blocked": sum(1 for event in event_list if event["type"] == "blocked"),
            "completed": sum(1 for event in event_list if event["type"] == "completed"),
            "milestones": sum(1 for event in event_list if event["type"] == "milestone"),
        },
        "tasks": public_tasks,
        "events": event_list,
    }


def write_json(data: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "dashboard.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_gantt_json(data: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "gantt.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def write_html(data: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "dashboard.html"
    summary = data["summary"]
    project_sections = "\n".join(project_html(project) for project in data["projects"])
    people_rows = "\n".join(
        f"<tr><td>{esc(person['person'])}</td><td>{person['events']}</td><td>{len(person['blockers'])}</td><td>{esc(', '.join(item['work_item'] for item in person['work_items'] if item.get('work_item')))}</td></tr>"
        for person in data["people"]
    )
    blocker_rows = "\n".join(
        f"<tr><td>{esc(item.get('project'))}</td><td>{esc(item.get('person'))}</td><td>{esc(item.get('work_item'))}</td><td>{esc(item.get('blocker'))}</td><td>{esc((item.get('source') or {}).get('source_id'))}</td></tr>"
        for item in data["blockers"]
    )
    timeline_rows = "\n".join(
        f"<tr><td>{esc(row.get('event_time'))}</td><td>{esc(row.get('project'))}</td><td>{esc(row.get('issue_key'))}</td><td>{esc(row.get('event_type'))}</td><td>{esc((row.get('source') or {}).get('table'))}</td></tr>"
        for row in data["timeline"]
    )
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Plane Demand Hub Dashboard</title>
  <style>
    :root {{ color-scheme: light; --ink:#20242a; --muted:#657282; --line:#d9dee7; --bg:#f7f8fa; --panel:#ffffff; --blue:#2f6fed; --green:#1b8a5a; --amber:#b26b00; --red:#c43d3d; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:var(--bg); }}
    header {{ padding:20px 28px 12px; border-bottom:1px solid var(--line); background:var(--panel); }}
    h1 {{ margin:0 0 6px; font-size:24px; letter-spacing:0; }}
    h2 {{ margin:26px 0 10px; font-size:18px; letter-spacing:0; }}
    h3 {{ margin:0 0 10px; font-size:16px; letter-spacing:0; }}
    main {{ padding:18px 28px 36px; max-width:1280px; margin:0 auto; }}
    .muted {{ color:var(--muted); font-size:13px; }}
    .summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }}
    .metric,.project {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:12px; }}
    .metric b {{ display:block; font-size:24px; margin-bottom:2px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:12px; }}
    table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
    th,td {{ padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; font-size:13px; }}
    th {{ color:var(--muted); font-weight:600; background:#fbfcfd; }}
    .badge {{ display:inline-block; border-radius:999px; padding:2px 8px; font-size:12px; border:1px solid var(--line); margin:0 4px 4px 0; }}
    .b-green {{ color:var(--green); border-color:#9fd6bf; }}
    .b-amber {{ color:var(--amber); border-color:#e3c28b; }}
    .b-red {{ color:var(--red); border-color:#e7a0a0; }}
    .bars {{ display:flex; gap:4px; align-items:center; flex-wrap:wrap; }}
    .bar {{ min-width:30px; padding:4px 6px; color:#fff; background:var(--blue); border-radius:4px; font-size:12px; text-align:center; }}
    ul {{ margin:8px 0 0; padding-left:18px; }}
    .section-table {{ overflow-x:auto; }}
  </style>
</head>
<body>
  <header>
    <h1>Plane Demand Hub Dashboard</h1>
    <div class="muted">Generated {esc(data['generated_at'])}. Sources: {summary['issues']} issues, {data['sources']['progress_audits']} progress audit(s).</div>
  </header>
  <main>
    <section class="summary">
      <div class="metric"><b>{summary['projects']}</b><span>Projects</span></div>
      <div class="metric"><b>{summary['issues']}</b><span>Work Items</span></div>
      <div class="metric"><b>{summary['people']}</b><span>People</span></div>
      <div class="metric"><b>{summary['blockers']}</b><span>Blockers</span></div>
      <div class="metric"><b>{summary['unresolved_drafts']}</b><span>Unresolved Drafts</span></div>
      <div class="metric"><b>{summary['stale_issues']}</b><span>Stale Items</span></div>
    </section>
    <h2>Projects</h2>
    <section class="grid">{project_sections}</section>
    <h2>People</h2>
    <div class="section-table"><table><thead><tr><th>Person</th><th>Updates</th><th>Blockers</th><th>Recent Work</th></tr></thead><tbody>{people_rows}</tbody></table></div>
    <h2>Blockers</h2>
    <div class="section-table"><table><thead><tr><th>Project</th><th>Person</th><th>Work</th><th>Blocker</th><th>Source</th></tr></thead><tbody>{blocker_rows}</tbody></table></div>
    <h2>Timeline</h2>
    <div class="section-table"><table><thead><tr><th>Time</th><th>Project</th><th>Issue</th><th>Event</th><th>Source Table</th></tr></thead><tbody>{timeline_rows}</tbody></table></div>
  </main>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")
    return path


def write_gantt_html(data: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "gantt.html"
    data_json = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    html_text = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Plane Demand Hub Gantt</title>
  <style>
    :root { color-scheme: light; --ink:#20242a; --muted:#657282; --line:#d9dee7; --bg:#f7f8fa; --panel:#ffffff; --blue:#2f6fed; --green:#1b8a5a; --amber:#b26b00; --red:#c43d3d; --row-h:30px; --bar-h:18px; --day-w:30px; --table-w:520px; --font-body:13px; --font-label:12px; --marker-size:20px; }
    body[data-density="present"] { --row-h:52px; --bar-h:28px; --day-w:40px; --table-w:620px; --font-body:15px; --font-label:13px; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:var(--bg); font-size:var(--font-body); letter-spacing:0; }
    header { display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; padding:16px 24px; border-bottom:1px solid var(--line); background:var(--panel); }
    h1 { margin:0; font-size:22px; line-height:1.2; font-weight:700; letter-spacing:0; }
    button { font:inherit; letter-spacing:0; }
    .meta { color:var(--muted); font-size:12px; margin-top:4px; }
    .toolbar { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
    .tool-button { min-width:36px; min-height:32px; border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:6px; padding:0 10px; cursor:pointer; }
    .tool-button[aria-pressed="true"] { border-color:var(--blue); color:var(--blue); box-shadow:0 0 0 2px rgba(47,111,237,.12); }
    main { padding:16px 24px 32px; }
    .summary { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; color:var(--muted); }
    .summary span { background:#fff; border:1px solid var(--line); border-radius:6px; padding:6px 8px; }
    .gantt-layout { display:grid; grid-template-columns:minmax(430px,var(--table-w)) minmax(560px,1fr); border:1px solid var(--line); background:var(--panel); min-height:520px; overflow:hidden; }
    .task-pane { border-right:1px solid var(--line); background:#fff; z-index:2; }
    .pane-head { height:34px; display:grid; align-items:center; border-bottom:1px solid var(--line); background:#fbfcfd; color:var(--muted); font-weight:600; font-size:12px; }
    .task-head { grid-template-columns:minmax(240px,1fr) 62px 64px 74px; }
    .task-head span, .task-row span { padding:0 6px; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .task-row { height:var(--row-h); display:grid; grid-template-columns:minmax(240px,1fr) 62px 64px 74px; align-items:center; border-bottom:1px solid var(--line); }
    .task-row.placeholder { background:#eef1f6; color:var(--muted); border:1px dashed #aeb8c7; transition:height .16s ease, background .16s ease; }
    .task-row.drop-parent { background:#eef5ff; box-shadow:inset 0 0 0 2px rgba(47,111,237,.2); }
    .task-main { display:flex; align-items:center; gap:4px; min-width:0; }
    .row-button { width:100%; min-height:calc(var(--row-h) - 6px); display:flex; align-items:center; gap:6px; border:0; background:transparent; color:var(--ink); text-align:left; cursor:pointer; padding:0 4px; border-radius:4px; overflow:hidden; }
    .task-row span:not(.task-main):not(.editable-cell) { cursor:pointer; }
    .editable-cell { cursor:text; }
    .row-button:focus-visible, .bar:focus-visible, .marker:focus-visible, .tool-button:focus-visible, .action-button:focus-visible, .danger-button:focus-visible, .palette-swatch:focus-visible { outline:2px solid var(--blue); outline-offset:2px; }
    .chevron { width:14px; flex:0 0 14px; color:var(--muted); text-align:center; }
    .task-key { color:var(--muted); flex:0 0 34px; width:34px; padding:0; font-size:11px; text-align:right; overflow:hidden; text-overflow:ellipsis; }
    .task-label { flex:1 1 auto; min-width:0; font-weight:600; font-size:var(--font-label); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .timeline-pane { overflow:auto; background:#fff; position:relative; }
    .timeline-content { position:relative; min-height:100%; }
    .time-head { height:34px; position:sticky; top:0; z-index:3; display:flex; border-bottom:1px solid var(--line); background:#fbfcfd; }
    .tick { width:var(--day-w); flex:0 0 var(--day-w); border-right:1px solid var(--line); padding:10px 1px 0; color:var(--muted); font-size:10px; text-align:center; white-space:nowrap; overflow:hidden; }
    .tick.weekend, .tick.holiday { background:#eef1f4; color:#7b8794; }
    .tick.holiday { box-shadow:inset 0 -2px 0 rgba(123,135,148,.34); }
    .timeline-row { height:var(--row-h); position:relative; border-bottom:1px solid var(--line); background-image:linear-gradient(to right, rgba(217,222,231,.72) 1px, transparent 1px); background-size:var(--day-w) 100%; }
    .bar { position:absolute; top:calc((var(--row-h) - var(--bar-h)) / 2); height:var(--bar-h); min-width:18px; border:0; border-radius:5px; background:var(--task-color,var(--blue)); color:#fff; padding:0 8px; display:flex; align-items:center; justify-content:flex-start; font-weight:650; font-size:var(--font-label); overflow:hidden; white-space:nowrap; cursor:pointer; box-shadow:inset 0 -1px 0 rgba(0,0,0,.18); }
    .bar-label { position:sticky; left:8px; max-width:calc(100% - 16px); z-index:1; overflow:hidden; text-overflow:ellipsis; pointer-events:none; }
    .bar.drop-parent { transform:scaleY(1.28); transform-origin:center; box-shadow:0 0 0 2px rgba(47,111,237,.22), inset 0 -1px 0 rgba(0,0,0,.18); }
    .bar-handle { position:absolute; top:0; bottom:0; width:10px; z-index:2; cursor:ew-resize; }
    .bar-handle.start { left:0; }
    .bar-handle.end { right:0; }
    .bar-handle:hover { background:rgba(255,255,255,.28); }
    .bar.parent { background:var(--task-color,var(--blue)); }
    .bar.blocked { background:var(--task-color,var(--red)); }
    .event-stack { position:absolute; top:50%; transform:translateY(-50%); min-height:calc(var(--marker-size) + 4px); display:flex; align-items:center; justify-content:center; gap:2px; padding:1px; border:1px solid rgba(154,165,180,.72); border-radius:999px; background:#fff; box-shadow:0 1px 3px rgba(32,36,42,.14); z-index:5; }
    .event-stack.multi { box-shadow:0 2px 6px rgba(32,36,42,.18); }
    .event-stack.collapsed { overflow:hidden; background:#fff; }
    .event-stack.expanded { min-height:26px; gap:4px; padding:2px 6px 2px 21px; border-color:var(--blue); border-radius:9px; background:#fff; box-shadow:0 0 0 2px rgba(47,111,237,.14), 0 4px 10px rgba(32,36,42,.12); z-index:7; }
    .stack-collapse { position:absolute; left:4px; top:50%; transform:translateY(-50%); width:13px; height:13px; border:1px solid #c8d1df; background:#fff; color:var(--blue); border-radius:999px; padding:0; display:flex; align-items:center; justify-content:center; font-size:10px; line-height:1; cursor:pointer; box-shadow:0 1px 2px rgba(32,36,42,.08); }
    .marker { width:var(--stack-marker-size, var(--marker-size)); height:var(--stack-marker-size, var(--marker-size)); border:1px solid var(--marker-color); background:var(--marker-color); color:#fff; border-radius:999px; display:flex; align-items:center; justify-content:center; padding:0; cursor:pointer; font-size:11px; font-weight:800; line-height:1; box-shadow:inset 0 -1px 0 rgba(0,0,0,.16); }
    .marker b { display:block; line-height:1; transform:translateY(-.25px); }
    .event-stack.collapsed .marker { position:absolute; top:50%; transform:translateY(-50%); }
    .event-stack.expanded .marker { position:relative; flex:0 0 auto; }
    .marker.blocked { --marker-color:var(--red); }
    .marker.in_progress { --marker-color:#6A8EC9; }
    .marker.completed { --marker-color:var(--green); }
    .marker.milestone { --marker-color:var(--amber); }
    .connector-layer { position:absolute; left:0; top:34px; pointer-events:none; overflow:visible; z-index:1; }
    .connector { fill:none; stroke:#9aa5b4; stroke-width:1.35; stroke-linecap:square; stroke-linejoin:miter; stroke-dasharray:5 4; opacity:.9; vector-effect:non-scaling-stroke; shape-rendering:geometricPrecision; mix-blend-mode:normal; }
    .timeline-row.placeholder { background:#eef1f6; border:1px dashed #aeb8c7; transition:height .16s ease, background .16s ease; }
    .timeline-row.drop-parent { background:#f0f6ff; }
    .drag-ghost { position:fixed; left:0; top:0; z-index:20; pointer-events:none; min-width:240px; max-width:420px; padding:8px 10px; background:#fff; border:1px solid #aeb8c7; border-radius:6px; box-shadow:0 12px 30px rgba(32,36,42,.22); font-weight:700; opacity:.96; transform:translate(-9999px,-9999px); }
    body.dragging-row { user-select:none; cursor:grabbing; }
    .empty { padding:24px; color:var(--muted); }
    .detail { position:fixed; top:0; right:0; width:min(420px,100vw); height:100vh; background:#fff; border-left:1px solid var(--line); box-shadow:-12px 0 24px rgba(32,36,42,.12); transform:translateX(105%); transition:transform .16s ease; z-index:8; display:flex; flex-direction:column; }
    .detail.open { transform:translateX(0); }
    .detail header { padding:16px; border-bottom:1px solid var(--line); }
    .detail h2 { margin:0; font-size:18px; line-height:1.25; letter-spacing:0; }
    .detail-body { padding:16px; overflow:auto; }
    .kv { display:grid; grid-template-columns:120px 1fr; gap:8px; padding:7px 0; border-bottom:1px solid var(--line); }
    .kv b { color:var(--muted); font-weight:600; }
    .source-list { margin:8px 0 0; padding-left:18px; color:var(--muted); }
    .detail-actions { margin-top:18px; padding-top:14px; border-top:1px solid var(--line); display:grid; gap:8px; }
    .action-button { width:100%; min-height:34px; border:1px solid #bfd0ef; background:#f6f9ff; color:var(--blue); border-radius:6px; padding:0 12px; font-weight:700; cursor:pointer; }
    .action-button:hover { background:#edf4ff; }
    .palette-label { color:var(--muted); font-weight:700; margin-top:2px; }
    .palette-grid { display:grid; grid-template-columns:repeat(8, minmax(26px,1fr)); gap:8px; }
    .palette-swatch { height:28px; border:1px solid rgba(32,36,42,.14); border-radius:7px; background:var(--swatch); cursor:pointer; box-shadow:inset 0 -1px 0 rgba(0,0,0,.16); }
    .palette-swatch[aria-pressed="true"] { box-shadow:0 0 0 2px rgba(47,111,237,.26), inset 0 -1px 0 rgba(0,0,0,.16); }
    .danger-button { width:100%; min-height:36px; border:1px solid #e49a9a; background:#fff5f5; color:var(--red); border-radius:6px; padding:0 12px; font-weight:700; cursor:pointer; }
    .danger-button:hover { background:#ffecec; }
    @media (max-width: 760px) {
      header, main { padding-left:12px; padding-right:12px; }
      .gantt-layout { grid-template-columns:minmax(430px,78vw) minmax(520px,1fr); overflow:auto; }
      .timeline-pane { overflow:visible; }
    }
  </style>
</head>
<body data-density="dense">
  <header>
    <div>
      <h1>Plane Demand Hub Gantt</h1>
      <div class="meta" id="generated"></div>
    </div>
    <div class="toolbar" aria-label="Gantt controls">
      <button class="tool-button" id="refresh" type="button">Refresh exports</button>
      <button class="tool-button" id="reset-edits" type="button">Reset local edits</button>
      <button class="tool-button" id="push-edits" type="button">Push changes</button>
      <button class="tool-button" id="export-report" type="button">输出报告</button>
      <button class="tool-button" id="add-task" type="button">新增任务条</button>
      <button class="tool-button" id="add-event" type="button">新增事件</button>
      <button class="tool-button" id="marker-demo" type="button">Demo markers</button>
      <button class="tool-button" id="expand-all" type="button" title="Expand all">Expand</button>
      <button class="tool-button" id="collapse-all" type="button" title="Collapse all">Collapse</button>
      <button class="tool-button" id="density-dense" type="button" aria-pressed="true">Dense</button>
      <button class="tool-button" id="density-present" type="button" aria-pressed="false">Present</button>
    </div>
  </header>
  <main>
    <section class="summary" id="summary"></section>
    <section class="gantt-layout" aria-label="Gantt chart">
      <div class="task-pane">
        <div class="pane-head task-head"><span>Task</span><span>Owner</span><span>State</span><span>Range</span></div>
        <div id="task-rows"></div>
      </div>
      <div class="timeline-pane" id="timeline-scroll">
        <div class="timeline-content" id="timeline-content">
          <div class="time-head" id="time-head"></div>
          <svg class="connector-layer" id="connector-layer" aria-hidden="true"></svg>
          <div id="timeline-rows"></div>
        </div>
      </div>
    </section>
    <section class="empty" id="empty" hidden>
      <h2>No Gantt data</h2>
      <p>Run the timeline and progress export commands, then rebuild the Gantt view.</p>
    </section>
  </main>
  <aside class="detail" id="detail" aria-label="Delivery summary" aria-hidden="true">
    <header>
      <button class="tool-button" id="detail-close" type="button">Close</button>
      <h2 id="detail-title">Delivery summary</h2>
    </header>
    <div class="detail-body" id="detail-body"></div>
  </aside>
  <script id="gantt-data" type="application/json">__DATA__</script>
  <script>
    const gantt = JSON.parse(document.getElementById('gantt-data').textContent);
    const STORAGE_KEY = 'plane-demand-hub-gantt-local-edits-v1';
    const collapsed = new Set();
    const DAY_MS = 86400000;
    const PAD_DAYS = 30;
    const symbol = { blocked: '✕', in_progress: '→', completed: '●', milestone: '★' };
    const eventTypeLabel = { blocked: '求助', in_progress: '进行中', completed: '完成', milestone: '里程碑' };
    const eventTypeOrder = { blocked: 0, in_progress: 1, completed: 2, milestone: 3 };
    const taskColorPalette = ['#458A74', '#018B38', '#D9A421', '#F5A216', '#57AF37', '#41B9C1', '#008B8B', '#4E5689', '#6A8EC9', '#652884', '#652884', '#8A7355', '#CC5B45', '#848484', '#E42320', '#B46DA9'];
    const defaultTaskColor = '#2f6fed';
    const blockedTaskColor = '#c43d3d';
    const staleStartDays = 2;
    const staleMinimumOpacity = 0.1;
    const staleFullFadeDays = 6;
    const holidayDates = new Set([
      '2026-01-01', '2026-01-02', '2026-01-03',
      '2026-02-15', '2026-02-16', '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22', '2026-02-23',
      '2026-04-04', '2026-04-05', '2026-04-06',
      '2026-05-01', '2026-05-02', '2026-05-03', '2026-05-04', '2026-05-05',
      '2026-06-19', '2026-06-20', '2026-06-21',
      '2026-09-25', '2026-09-26', '2026-09-27',
      '2026-10-01', '2026-10-02', '2026-10-03', '2026-10-04', '2026-10-05', '2026-10-06', '2026-10-07'
    ]);
    const fixedHolidayMonthDays = new Set(['01-01', '05-01', '10-01']);
    const clone = value => JSON.parse(JSON.stringify(value));
    let tasks = clone(gantt.tasks);
    let events = clone(gantt.events);
    let tasksById = new Map();
    let dragState = null;
    let suppressNextClick = false;
    const expandedEventStacks = new Set();
    let activeMinOrd = 0;
    let activeMaxOrd = 0;
    let selectedTaskId = null;
    let didCenterToday = false;

    restoreEdits();
    rebuildTaskIndex();

    function dateOrd(value) {
      if (!value) return null;
      const parsed = Date.parse(value.length === 10 ? value + 'T00:00:00Z' : value);
      return Number.isNaN(parsed) ? null : Math.floor(parsed / DAY_MS);
    }
    function isoFromOrd(ord) {
      return new Date(ord * DAY_MS).toISOString().slice(0, 10);
    }
    function todayOrd() {
      return dateOrd(new Date().toISOString().slice(0, 10));
    }
    function isWeekendOrd(ord) {
      const day = new Date(ord * DAY_MS).getUTCDay();
      return day === 0 || day === 6;
    }
    function isHolidayDate(isoDate) {
      return holidayDates.has(isoDate) || fixedHolidayMonthDays.has(isoDate.slice(5));
    }
    function updateBounds() {
      const ords = [];
      for (const task of tasks) {
        const start = dateOrd(task.start_date);
        const target = dateOrd(task.target_date);
        if (start !== null) ords.push(start);
        if (target !== null) ords.push(target);
      }
      const fallback = todayOrd();
      activeMinOrd = (ords.length ? Math.min(...ords) : fallback) - PAD_DAYS;
      activeMaxOrd = (ords.length ? Math.max(...ords) : fallback) + PAD_DAYS;
    }
    function restoreEdits() {
      try {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
        if (!saved) return;
        const deletedTaskIds = new Set(saved.deleted_task_ids || []);
        const deletedEventIds = new Set(saved.deleted_event_ids || []);
        const baseTasks = tasks.filter(task => !deletedTaskIds.has(task.id));
        const baseTaskIds = new Set(baseTasks.map(task => task.id));
        const savedTasks = new Map((saved.tasks || []).map(task => [task.id, task]));
        const mergedTasks = new Map(baseTasks.map(task => [task.id, Object.assign(task, savedTasks.get(task.id) || {})]));
        for (const task of saved.tasks || []) {
          if (!baseTaskIds.has(task.id) && !deletedTaskIds.has(task.id)) mergedTasks.set(task.id, task);
        }
        const orderedTasks = [];
        const seenTasks = new Set();
        for (const savedTask of saved.tasks || []) {
          const task = mergedTasks.get(savedTask.id);
          if (!task || seenTasks.has(task.id)) continue;
          orderedTasks.push(task);
          seenTasks.add(task.id);
        }
        for (const task of baseTasks) {
          if (seenTasks.has(task.id)) continue;
          orderedTasks.push(mergedTasks.get(task.id) || task);
        }
        tasks = orderedTasks;
        const baseEvents = new Map(events.filter(event => !deletedEventIds.has(event.id)).map(event => [event.id, event]));
        for (const event of saved.events || []) {
          if (!deletedEventIds.has(event.id)) baseEvents.set(event.id, event);
        }
        events = [...baseEvents.values()];
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    function persistEdits() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        tasks: tasks.map((task, index) => taskStorageRecord(task, index)),
        events,
        deleted_task_ids: deletedTaskIds(),
        deleted_event_ids: deletedEventIds()
      }));
    }
    function taskStorageRecord(task, index = 0) {
      return {
        id: task.id,
        issue_id: task.issue_id || null,
        issue_key: task.issue_key || null,
        title: task.title,
        compact_label: task.compact_label,
        parent_id: task.parent_id || null,
        children: task.children || [],
        depth: task.depth || 0,
        order: task.order || 0,
        order_index: index,
        project: task.project || null,
        state: task.state || null,
        priority: task.priority || null,
        progress: task.progress || 0,
        owner: task.owner || null,
        color: task.color || null,
        labels: task.labels || [],
        modules: task.modules || [],
        start_date: task.start_date || null,
        target_date: task.target_date || null,
        completed_at: task.completed_at || null,
        source_refs: task.source_refs || [],
        delivery_summary: task.delivery_summary || {}
      };
    }
    function baseTaskMap() {
      return new Map(gantt.tasks.map(task => [task.id, task]));
    }
    function baseEventMap() {
      return new Map(gantt.events.map(event => [event.id, event]));
    }
    function changedTaskRecords() {
      const base = baseTaskMap();
      return tasks
        .map((task, index) => {
          const original = base.get(task.id);
          if (!original) return null;
          const changes = {};
          for (const key of ['title', 'compact_label', 'parent_id', 'start_date', 'target_date', 'owner', 'state', 'progress', 'labels', 'modules', 'color', 'delivery_summary']) {
            if (!sameValue(task[key], original[key])) changes[key] = task[key] ?? null;
          }
          const originalOrder = gantt.tasks.findIndex(item => item.id === task.id);
          if (originalOrder !== -1 && originalOrder !== index) changes.order_index = index;
          return Object.keys(changes).length ? {
            id: task.id,
            issue_id: task.issue_id,
            issue_key: task.issue_key,
            changes
          } : null;
        })
        .filter(Boolean);
    }
    function newTaskRecords() {
      const base = baseTaskMap();
      return tasks
        .filter(task => !base.has(task.id))
        .map(task => ({
          id: task.id,
          issue_id: task.issue_id || null,
          issue_key: task.issue_key || null,
          title: task.title,
          compact_label: task.compact_label,
          parent_id: task.parent_id || null,
          order_index: tasks.findIndex(item => item.id === task.id),
          project: task.project || null,
          state: task.state || null,
          progress: task.progress || 0,
          owner: task.owner || null,
          color: task.color || null,
          labels: task.labels || [],
          modules: task.modules || [],
          start_date: task.start_date || null,
          target_date: task.target_date || null,
          delivery_summary: task.delivery_summary || {},
          source_refs: task.source_refs || []
        }));
    }
    function newEventRecords() {
      const base = baseEventMap();
      return events
        .filter(event => !base.has(event.id))
        .map(event => ({
          id: event.id,
          task_id: event.task_id,
          type: event.type,
          date: event.date,
          summary: event.summary,
          compact_label: event.compact_label,
          source_refs: event.source_refs || []
        }));
    }
    function changedEventRecords() {
      const base = baseEventMap();
      return events
        .map(event => {
          const original = base.get(event.id);
          if (!original) return null;
          const changes = {};
          for (const key of ['task_id', 'type', 'date', 'summary', 'compact_label']) {
            if (!sameValue(event[key], original[key])) changes[key] = event[key] ?? null;
          }
          return Object.keys(changes).length ? {
            id: event.id,
            task_id: event.task_id,
            changes
          } : null;
        })
        .filter(Boolean);
    }
    function deletedTaskIds() {
      const current = new Set(tasks.map(task => task.id));
      return gantt.tasks.filter(task => !current.has(task.id)).map(task => task.id);
    }
    function deletedEventIds() {
      const current = new Set(events.map(event => event.id));
      return gantt.events.filter(event => !current.has(event.id)).map(event => event.id);
    }
    function deletedTaskRecords() {
      const current = new Set(tasks.map(task => task.id));
      return gantt.tasks
        .filter(task => !current.has(task.id))
        .map(task => ({
          id: task.id,
          issue_id: task.issue_id,
          issue_key: task.issue_key,
          title: task.title
        }));
    }
    function deletedEventRecords() {
      const current = new Set(events.map(event => event.id));
      return gantt.events
        .filter(event => !current.has(event.id))
        .map(event => ({
          id: event.id,
          task_id: event.task_id,
          type: event.type,
          date: event.date,
          summary: event.summary
        }));
    }
    function buildChangeset() {
      return {
        schema: 'plane-demand-hub.gantt-edits.v1',
        generated_at: new Date().toISOString(),
        source_gantt_generated_at: gantt.generated_at,
        note: 'Static Gantt edits are persisted as an auditable changeset. Applying to Plane requires a controlled API writer; no direct Plane database writes.',
        new_tasks: newTaskRecords(),
        task_changes: changedTaskRecords(),
        event_changes: changedEventRecords(),
        new_events: newEventRecords(),
        deleted_tasks: deletedTaskRecords(),
        deleted_events: deletedEventRecords(),
        snapshot: {
          tasks: tasks.map((task, index) => ({
            id: task.id,
            issue_id: task.issue_id,
            issue_key: task.issue_key,
            title: task.title,
            compact_label: task.compact_label,
            parent_id: task.parent_id,
            order_index: index,
            owner: task.owner,
            state: task.state,
            progress: task.progress,
            labels: task.labels || [],
            modules: task.modules || [],
            color: task.color || null,
            delivery_summary: task.delivery_summary || {},
            start_date: task.start_date,
            target_date: task.target_date
          })),
          events
        }
      };
    }
    function downloadJson(filename, payload) {
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.append(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(link.href);
    }
    function downloadText(filename, content, type = 'text/markdown') {
      const blob = new Blob([content], { type: `${type};charset=utf-8` });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.append(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(link.href);
    }
    function addDays(value, days) {
      return isoFromOrd((dateOrd(value) ?? todayOrd()) + days);
    }
    function reportKindFromInput(value) {
      const raw = String(value || '').trim().toLowerCase();
      if (raw.includes('周') || raw.includes('week')) return 'weekly';
      if (raw.includes('月') || raw.includes('month')) return 'monthly';
      return 'daily';
    }
    function reportKindLabel(kind) {
      return { daily: '日报', weekly: '周报', monthly: '月报' }[kind] || '日报';
    }
    function defaultReportPeriod(kind) {
      const today = todayOrd();
      if (kind === 'weekly') {
        const date = new Date(today * DAY_MS);
        const day = date.getUTCDay() || 7;
        const start = today - day + 1;
        return { start: isoFromOrd(start), end: isoFromOrd(start + 6) };
      }
      if (kind === 'monthly') {
        const date = new Date(today * DAY_MS);
        const start = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1) / DAY_MS;
        const end = Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0) / DAY_MS;
        return { start: isoFromOrd(start), end: isoFromOrd(end) };
      }
      const day = isoFromOrd(today);
      return { start: day, end: day };
    }
    function dateInRange(value, startDate, endDate) {
      const ord = dateOrd(value);
      return ord !== null && ord >= dateOrd(startDate) && ord <= dateOrd(endDate);
    }
    function taskOverlapsPeriod(task, startDate, endDate, periodEvents) {
      const start = dateOrd(task.start_date);
      const target = dateOrd(task.target_date) ?? start;
      const periodStart = dateOrd(startDate);
      const periodEnd = dateOrd(endDate);
      const rangeOverlaps = start !== null && target !== null && start <= periodEnd && target >= periodStart;
      return rangeOverlaps || periodEvents.some(event => event.task_id === task.id);
    }
    function cleanReportText(value) {
      const raw = text(value);
      return raw === 'n/a' ? '' : raw.replace(/\\s+/g, ' ').trim();
    }
    function taskName(task) {
      return `${cleanReportText(task.issue_key)} ${cleanReportText(task.title)}`.trim();
    }
    function pushLine(lines, value) {
      if (value) lines.push(value);
    }
    function buildReportMarkdown(kind, startDate, endDate) {
      const label = reportKindLabel(kind);
      const periodEvents = sortedEvents(events.filter(event => dateInRange(event.date, startDate, endDate)));
      const reportTasks = tasks.filter(task => taskOverlapsPeriod(task, startDate, endDate, periodEvents));
      const lines = [
        `# Plane Demand Hub ${label}`,
        '',
        `周期：${startDate} 至 ${endDate}`,
        `生成时间：${new Date().toISOString()}`,
        `数据来源：当前 Gantt 页面状态（含本地编辑）`,
        '',
        '## 进展'
      ];
      if (!reportTasks.length) {
        lines.push('- 本周期没有匹配任务。');
      } else {
        for (const task of reportTasks) {
          const taskEvents = periodEvents.filter(event => event.task_id === task.id);
          const eventText = taskEvents.map(event => `${eventLabel(event.type)} ${shortDate(event.date)} ${cleanReportText(event.summary)}`).join('；');
          const range = `${cleanReportText(task.start_date)}→${cleanReportText(task.target_date)}`;
          const owner = cleanReportText(task.owner) || '未分配';
          const progress = `${text(task.progress)}%`;
          lines.push(`- ${taskName(task)}：${stateText(task.state)}，进度 ${progress}，Owner ${owner}，周期 ${range}${eventText ? `；事件：${eventText}` : ''}`);
        }
      }
      lines.push('', '## 下一步');
      const nextLines = reportTasks
        .map(task => ({ task, next: cleanReportText((task.delivery_summary || {}).next_action) }))
        .filter(item => item.next);
      if (!nextLines.length) lines.push('- 暂无明确下一步。');
      for (const item of nextLines) lines.push(`- ${taskName(item.task)}：${item.next}`);

      lines.push('', '## 阻塞');
      const blockerLines = [];
      for (const task of reportTasks) {
        const summary = task.delivery_summary || {};
        const blocker = cleanReportText(summary.blocker);
        const isBlocked = stateText(task.state) === '阻塞' || (task.labels || []).some(label => ['blocked', 'needs-help', 'blocker'].includes(String(label).toLowerCase()));
        if (blocker || isBlocked) blockerLines.push(`- ${taskName(task)}：${blocker || '状态或标签显示阻塞'}`);
      }
      if (!blockerLines.length) lines.push('- 暂无阻塞。');
      else lines.push(...blockerLines);

      lines.push('', '## 求助点');
      const helpEvents = periodEvents.filter(event => event.type === 'blocked');
      if (!helpEvents.length) {
        lines.push('- 暂无求助点。');
      } else {
        for (const event of helpEvents) {
          const task = tasksById.get(event.task_id) || {};
          lines.push(`- ${taskName(task)}：${shortDate(event.date)} ${cleanReportText(event.summary) || '需要协助'}`);
        }
      }
      lines.push('', '## 事件明细');
      if (!periodEvents.length) {
        lines.push('- 本周期没有事件标记。');
      } else {
        for (const event of periodEvents) {
          const task = tasksById.get(event.task_id) || {};
          lines.push(`- ${shortDate(event.date)} · ${eventLabel(event.type)} · ${taskName(task)} · ${cleanReportText(event.summary)}`);
        }
      }
      return lines.join('\\n') + '\\n';
    }
    function exportReport() {
      persistEdits();
      rebuildTaskIndex();
      const rawKind = prompt('报告类型：日报 / 周报 / 月报', '日报');
      if (rawKind === null) return;
      const kind = reportKindFromInput(rawKind);
      const defaults = defaultReportPeriod(kind);
      const startDate = promptDate('开始日期 YYYY-MM-DD', defaults.start);
      if (!startDate) return;
      const endDate = promptDate('结束日期 YYYY-MM-DD', defaults.end);
      if (!endDate) return;
      const startOrd = dateOrd(startDate) ?? todayOrd();
      const endOrd = dateOrd(endDate) ?? startOrd;
      const normalizedStart = isoFromOrd(Math.min(startOrd, endOrd));
      const normalizedEnd = isoFromOrd(Math.max(startOrd, endOrd));
      const markdown = buildReportMarkdown(kind, normalizedStart, normalizedEnd);
      const filename = `gantt-${kind}-report-${normalizedStart}-to-${normalizedEnd}.md`;
      downloadText(filename, markdown);
    }
    async function pushEdits() {
      persistEdits();
      const changeset = buildChangeset();
      if (!changeset.new_tasks.length && !changeset.task_changes.length && !changeset.event_changes.length && !changeset.new_events.length && !changeset.deleted_tasks.length && !changeset.deleted_events.length) {
        alert('没有可 Push 的本地修改。');
        return;
      }
      const filename = `gantt-changeset-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
      try {
        const response = await fetch('/api/gantt-edits', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename, changeset })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        alert(`已保存 changeset：${result.path || filename}\\n注意：这还不是 Plane API 写回。`);
      } catch (error) {
        downloadJson(filename, changeset);
        alert('当前服务器不支持直接写文件，已下载 changeset JSON。真正写回 Plane 仍需受控 API writer。');
      }
    }
    function rebuildTaskIndex() {
      tasksById = new Map(tasks.map(task => [task.id, task]));
      for (const task of tasks) task.children = [];
      for (const task of tasks) {
        if (task.parent_id && tasksById.has(task.parent_id) && task.parent_id !== task.id) {
          tasksById.get(task.parent_id).children.push(task.id);
        } else if (task.parent_id && !tasksById.has(task.parent_id)) {
          task.parent_id = null;
        }
      }
      const assignDepth = (task, depth, seen = new Set()) => {
        if (!task || seen.has(task.id)) return;
        seen.add(task.id);
        task.depth = depth;
        for (const childId of task.children || []) assignDepth(tasksById.get(childId), depth + 1, seen);
      };
      for (const task of tasks) if (!task.parent_id) assignDepth(task, 0);
    }
    function eventsByTask() {
      const map = new Map();
      for (const event of events) {
        if (!map.has(event.task_id)) map.set(event.task_id, []);
        map.get(event.task_id).push(event);
      }
      return map;
    }
    function isLocalTask(task) {
      return String(task?.id || '').startsWith('local-task:') || (task?.labels || []).includes('local') || task?.issue_key === 'NEW';
    }
    function isFreshnessSourceRef(ref) {
      return ref?.event_type !== 'local_task_created';
    }
    function localTaskFallbackOrd(task) {
      if (!isLocalTask(task)) return null;
      return dateOrd(task.start_date) ?? dateOrd(task.target_date);
    }
    function eventActivityOrds(event) {
      const ords = [];
      const eventOrd = dateOrd(event.date);
      if (eventOrd !== null) ords.push(eventOrd);
      for (const ref of event.source_refs || []) {
        const refOrd = dateOrd(ref.event_time);
        if (refOrd !== null) ords.push(refOrd);
      }
      return ords;
    }
    function directTaskActivityOrds(task, taskEvents = []) {
      const ords = [];
      for (const event of taskEvents) {
        ords.push(...eventActivityOrds(event));
      }
      const completedOrd = dateOrd(task.completed_at);
      if (completedOrd !== null) ords.push(completedOrd);
      for (const ref of task.source_refs || []) {
        if (!isFreshnessSourceRef(ref)) continue;
        const ord = dateOrd(ref.event_time);
        if (ord !== null) ords.push(ord);
      }
      if (!ords.length) {
        const fallback = localTaskFallbackOrd(task);
        if (fallback !== null) ords.push(fallback);
      }
      return ords;
    }
    function latestTaskEventOrd(task, taskEventsOrMap = [], seen = new Set()) {
      if (!task || seen.has(task.id)) return null;
      seen.add(task.id);
      const byTask = taskEventsOrMap instanceof Map ? taskEventsOrMap : new Map([[task.id, taskEventsOrMap]]);
      const ords = directTaskActivityOrds(task, byTask.get(task.id) || []);
      for (const childId of task.children || []) {
        const child = tasksById.get(childId);
        const childOrd = latestTaskEventOrd(child, byTask, seen);
        if (childOrd !== null) ords.push(childOrd);
      }
      return ords.length ? Math.max(...ords) : null;
    }
    function taskLastEventAgeDays(task, taskEventsOrMap = []) {
      const last = latestTaskEventOrd(task, taskEventsOrMap);
      return last === null ? null : Math.max(0, todayOrd() - last);
    }
    function taskFreshnessOpacity(task, taskEventsOrMap = []) {
      const age = taskLastEventAgeDays(task, taskEventsOrMap);
      if (age === null || age < staleStartDays) return 1;
      if (age >= staleFullFadeDays) return staleMinimumOpacity;
      const span = Math.max(1, staleFullFadeDays - staleStartDays + 1);
      const ratio = Math.min(1, (age - staleStartDays + 1) / span);
      return Math.max(staleMinimumOpacity, 1 - ratio * (1 - staleMinimumOpacity));
    }
    function taskBaseColor(task) {
      const labels = task.labels || [];
      if (task.color) return task.color;
      if (labels.includes('blocked') || labels.includes('needs-help')) return blockedTaskColor;
      return defaultTaskColor;
    }
    function hexToRgba(hex, alpha) {
      const raw = String(hex || '').trim().replace('#', '');
      const normalized = raw.length === 3 ? raw.split('').map(char => char + char).join('') : raw;
      if (!/^[0-9a-fA-F]{6}$/.test(normalized)) return hex;
      const value = Number.parseInt(normalized, 16);
      const red = (value >> 16) & 255;
      const green = (value >> 8) & 255;
      const blue = value & 255;
      return `rgba(${red}, ${green}, ${blue}, ${alpha.toFixed(3)})`;
    }
    function taskStaleTitle(task, taskEventsOrMap = []) {
      const age = taskLastEventAgeDays(task, taskEventsOrMap);
      if (age === null) return '暂无事件记录';
      if (age < staleStartDays) return `最近事件 ${age} 天前`;
      return `最近事件 ${age} 天前，颜色已淡化提醒关注`;
    }
    function summarize() {
      return {
        tasks: tasks.length,
        parent_links: tasks.filter(task => task.parent_id).length,
        events: events.length,
        blocked: events.filter(event => event.type === 'blocked').length,
        in_progress: events.filter(event => event.type === 'in_progress').length,
        completed: events.filter(event => event.type === 'completed').length,
        milestones: events.filter(event => event.type === 'milestone').length
      };
    }

    function hiddenByAncestor(task) {
      let parentId = task.parent_id;
      while (parentId) {
        if (collapsed.has(parentId)) return true;
        const parent = tasksById.get(parentId);
        parentId = parent && parent.parent_id;
      }
      return false;
    }
    function visibleTasks() {
      rebuildTaskIndex();
      return tasks.filter(task => !hiddenByAncestor(task));
    }
    function rowHeight() {
      return parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--row-h')) || 30;
    }
    function dayWidth() {
      return parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--day-w')) || 28;
    }
    function offsetForDate(value) {
      const ord = dateOrd(value);
      return Math.max(0, ((ord ?? activeMinOrd) - activeMinOrd) * dayWidth());
    }
    function widthForTask(task) {
      const start = dateOrd(task.start_date) ?? activeMinOrd;
      const target = dateOrd(task.target_date) ?? start;
      return Math.max(dayWidth(), (target - start + 1) * dayWidth());
    }
    function text(value) {
      return value === null || value === undefined || value === '' ? 'n/a' : String(value);
    }
    function sameValue(left, right) {
      const normalize = value => {
        if (value === undefined || value === null || value === '') return null;
        if (Array.isArray(value) || typeof value === 'object') return JSON.stringify(value);
        return String(value);
      };
      return normalize(left) === normalize(right);
    }
    function compact(value) {
      return text(value).slice(0, 8);
    }
    function compactTaskLabel(value) {
      let label = text(value).replace(/^\\s*(?:\\d{4}[-/.]\\d{1,2}[-/.]\\d{1,2}|\\d{4}\\s+Q\\d)\\s*/, '').trim();
      if (label.includes('：')) label = label.split('：').slice(1).join('：').trim() || label;
      else if (label.includes(': ')) label = label.split(': ').slice(1).join(': ').trim() || label;
      return compact(label);
    }
    function eventLabel(type) {
      return eventTypeLabel[type] || type || '事件';
    }
    function sortedEvents(eventList) {
      return [...eventList].sort((left, right) => (
        text(left.date).localeCompare(text(right.date)) ||
        ((eventTypeOrder[left.type] ?? 9) - (eventTypeOrder[right.type] ?? 9)) ||
        text(left.id).localeCompare(text(right.id))
      ));
    }
    function shouldSuppressClick(event) {
      if (!suppressNextClick) return false;
      suppressNextClick = false;
      event.preventDefault();
      event.stopPropagation();
      return true;
    }
    function eventStackKey(taskId, eventDate) {
      return `${taskId}:${eventDate || 'n/a'}`;
    }
    function markerSize() {
      return parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--marker-size')) || 20;
    }
    function dateObj(value) {
      const ord = dateOrd(value);
      return ord === null ? null : new Date(ord * DAY_MS);
    }
    function monthText(value) {
      const date = dateObj(value);
      return date ? `M${date.getUTCMonth() + 1}` : 'n/a';
    }
    function monthRange(task) {
      const start = monthText(task.start_date);
      const target = monthText(task.target_date);
      if (start === 'n/a' && target === 'n/a') return 'n/a';
      if (start === target || target === 'n/a') return start;
      if (start === 'n/a') return target;
      return `${start}～${target}`;
    }
    function shortDate(value) {
      const date = dateObj(value);
      return date ? `${date.getUTCMonth() + 1}/${date.getUTCDate()}` : 'n/a';
    }
    function stateText(value) {
      const raw = text(value);
      const lower = raw.toLowerCase();
      if (['done', 'completed', 'complete', 'closed', '已完成', '完成'].includes(lower) || lower.includes('done')) return '完成';
      if (['todo', 'backlog', '待办'].includes(lower)) return '待办';
      if (lower.includes('blocked') || lower.includes('waiting') || lower.includes('stuck') || raw.includes('阻塞') || raw.includes('等待')) return '阻塞';
      if (raw === 'n/a') return 'n/a';
      return '进行中';
    }
    function setDensity(mode) {
      document.body.dataset.density = mode;
      document.getElementById('density-dense').setAttribute('aria-pressed', mode === 'dense');
      document.getElementById('density-present').setAttribute('aria-pressed', mode === 'present');
      expandedEventStacks.clear();
      render();
    }
    function makeCell(value, title) {
      const span = document.createElement('span');
      span.textContent = text(value);
      span.title = text(title ?? value);
      return span;
    }
    function makeOwnerCell(task) {
      const span = makeCell(task.owner);
      span.classList.add('editable-cell');
      span.title = `双击修改 Owner：${text(task.owner)}`;
      span.addEventListener('dblclick', event => {
        event.preventDefault();
        event.stopPropagation();
        editTaskOwner(task);
      });
      return span;
    }
    function handleTaskRowClick(event, task) {
      if (shouldSuppressClick(event)) return;
      if (event.target?.closest?.('.editable-cell')) return;
      event.stopPropagation();
      toggleTask(task);
      showTask(task);
    }
    function subtreeIds(taskId, ids = new Set()) {
      if (!taskId || ids.has(taskId)) return ids;
      ids.add(taskId);
      const task = tasksById.get(taskId);
      for (const childId of task?.children || []) subtreeIds(childId, ids);
      return ids;
    }
    function ordFromPointer(event) {
      const pane = document.getElementById('timeline-scroll');
      const rect = pane.getBoundingClientRect();
      const x = event.clientX - rect.left + pane.scrollLeft;
      return activeMinOrd + Math.round(x / dayWidth());
    }
    function setTaskDate(task, edge, ord) {
      const start = dateOrd(task.start_date) ?? ord;
      const target = dateOrd(task.target_date) ?? start;
      if (edge === 'start') {
        const next = Math.min(ord, target);
        task.start_date = isoFromOrd(next);
      } else {
        const next = Math.max(ord, start);
        task.target_date = isoFromOrd(next);
      }
      task.delivery_summary = task.delivery_summary || {};
      task.delivery_summary.date_range = `${text(task.start_date)} - ${text(task.target_date)}`;
    }
    function closeDetail() {
      const detail = document.getElementById('detail');
      detail.classList.remove('open');
      detail.setAttribute('aria-hidden', 'true');
    }
    function openDetail(title, rows, refs, options = {}) {
      document.getElementById('detail-title').textContent = title || 'Delivery summary';
      const body = document.getElementById('detail-body');
      body.replaceChildren();
      for (const [key, value] of rows) {
        const row = document.createElement('div');
        row.className = 'kv';
        const label = document.createElement('b');
        label.textContent = key;
        const content = document.createElement('span');
        content.textContent = text(value);
        row.append(label, content);
        body.append(row);
      }
      const actionsList = options.actions || [];
      const dangerAction = options.dangerAction;
      if (actionsList.length || options.palette || dangerAction) {
        const actions = document.createElement('div');
        actions.className = 'detail-actions';
        for (const action of actionsList) {
          const button = document.createElement('button');
          button.className = 'action-button';
          button.type = 'button';
          button.textContent = action.label;
          button.addEventListener('click', action.onClick);
          actions.append(button);
        }
        if (options.palette) {
          const label = document.createElement('div');
          label.className = 'palette-label';
          label.textContent = options.palette.label;
          actions.append(label);
          const palette = document.createElement('div');
          palette.className = 'palette-grid';
          for (const color of options.palette.colors) {
            const swatch = document.createElement('button');
            swatch.className = 'palette-swatch';
            swatch.type = 'button';
            swatch.style.setProperty('--swatch', color);
            swatch.title = color;
            swatch.setAttribute('aria-label', color);
            swatch.setAttribute('aria-pressed', color.toLowerCase() === String(options.palette.value || '').toLowerCase());
            swatch.addEventListener('click', () => options.palette.onSelect(color));
            palette.append(swatch);
          }
          actions.append(palette);
        }
        if (dangerAction) {
          const danger = document.createElement('button');
          danger.className = 'danger-button';
          danger.type = 'button';
          danger.textContent = dangerAction.label;
          danger.addEventListener('click', dangerAction.onClick);
          actions.append(danger);
        }
        body.append(actions);
      }
      const heading = document.createElement('h3');
      heading.textContent = 'Source evidence';
      body.append(heading);
      const list = document.createElement('ul');
      list.className = 'source-list';
      for (const ref of (refs || []).slice(0, 12)) {
        const item = document.createElement('li');
        const source = ref.source || {};
        item.textContent = `${text(ref.event_time)} · ${text(ref.event_type)} · ${text(source.table)} ${text(source.field || source.id)}`;
        list.append(item);
      }
      body.append(list);
      const detail = document.getElementById('detail');
      detail.classList.add('open');
      detail.setAttribute('aria-hidden', 'false');
    }
    function showTask(task) {
      selectedTaskId = task.id;
      const summary = task.delivery_summary || {};
      openDetail(summary.title || task.title, [
        ['Task', `${text(task.issue_key)} ${text(task.title)}`],
        ['Owner', task.owner],
        ['State', stateText(task.state)],
        ['Progress', `${text(task.progress)}%`],
        ['Range', monthRange(task)],
        ['Blocker', summary.blocker],
        ['Next action', summary.next_action],
        ['Labels', (task.labels || []).join(', ')],
        ['Modules', (task.modules || []).join(', ')],
        ['Color', task.color || '默认']
      ], task.source_refs, {
        actions: [{ label: '编辑任务字段', onClick: () => editTaskFields(task) }],
        palette: { label: '任务条颜色', value: task.color, colors: taskColorPalette, onSelect: color => setTaskColor(task, color) },
        dangerAction: { label: '删除任务', onClick: () => deleteTask(task) }
      });
    }
    function showEvent(event) {
      const task = tasksById.get(event.task_id) || {};
      selectedTaskId = event.task_id;
      openDetail(event.summary || 'Delivery summary', [
        ['Event', eventLabel(event.type)],
        ['Task', `${text(task.issue_key)} ${text(task.title)}`],
        ['Date', shortDate(event.date)],
        ['Summary', event.summary],
        ['Owner', task.owner],
        ['State', stateText(task.state)],
        ['Next action', (task.delivery_summary || {}).next_action]
      ], event.source_refs, {
        actions: [{ label: '修改事件', onClick: () => editEvent(event) }],
        dangerAction: { label: '删除事件', onClick: () => deleteEvent(event) }
      });
    }
    function toggleTask(task) {
      if (!task.children || task.children.length === 0) return;
      if (collapsed.has(task.id)) collapsed.delete(task.id);
      else collapsed.add(task.id);
      render();
    }
    function editTaskName(task) {
      const next = prompt('修改任务名称', task.title || '');
      if (next === null) return;
      const title = next.trim();
      if (!title) return;
      task.title = title;
      task.compact_label = compactTaskLabel(title);
      task.delivery_summary = task.delivery_summary || {};
      task.delivery_summary.title = title;
      persistEdits();
      render();
    }
    function editTaskOwner(task) {
      const next = prompt('修改 Owner', task.owner || '');
      if (next === null) return;
      task.owner = next.trim() || null;
      persistEdits();
      render();
      showTask(task);
    }
    function parseList(value) {
      return String(value || '')
        .split(',')
        .map(item => item.trim())
        .filter(Boolean);
    }
    function setTaskColor(task, color) {
      task.color = color;
      persistEdits();
      render();
      showTask(task);
    }
    function editTaskFields(task) {
      const summary = task.delivery_summary || {};
      const rawTitle = prompt('Task', task.title || '');
      if (rawTitle === null) return;
      const title = rawTitle.trim();
      if (!title) {
        alert('任务名称不能为空。');
        return;
      }
      const owner = prompt('Owner', task.owner || '');
      if (owner === null) return;
      const state = prompt('State', task.state || '');
      if (state === null) return;
      const rawProgress = prompt('Progress 0-100', String(task.progress ?? 0));
      if (rawProgress === null) return;
      const progress = Math.max(0, Math.min(100, Number.parseInt(rawProgress, 10) || 0));
      const startDate = promptDate('开始日期 YYYY-MM-DD', task.start_date || isoFromOrd(todayOrd()));
      if (!startDate) return;
      const targetDate = promptDate('结束日期 YYYY-MM-DD', task.target_date || startDate);
      if (!targetDate) return;
      const blocker = prompt('Blocker', summary.blocker || '');
      if (blocker === null) return;
      const nextAction = prompt('Next action', summary.next_action || '');
      if (nextAction === null) return;
      const labels = prompt('Labels，用英文逗号分隔', (task.labels || []).join(', '));
      if (labels === null) return;
      const modules = prompt('Modules，用英文逗号分隔', (task.modules || []).join(', '));
      if (modules === null) return;
      const startOrd = dateOrd(startDate) ?? todayOrd();
      const targetOrd = dateOrd(targetDate) ?? startOrd;
      task.title = title;
      task.compact_label = compactTaskLabel(title);
      task.owner = owner.trim() || null;
      task.state = state.trim() || null;
      task.progress = progress;
      task.start_date = isoFromOrd(Math.min(startOrd, targetOrd));
      task.target_date = isoFromOrd(Math.max(startOrd, targetOrd));
      task.labels = parseList(labels);
      task.modules = parseList(modules);
      task.delivery_summary = Object.assign({}, summary, {
        title,
        blocker: blocker.trim() || null,
        next_action: nextAction.trim() || null,
        date_range: `${text(task.start_date)} - ${text(task.target_date)}`
      });
      persistEdits();
      render();
      showTask(task);
    }
    function taskSearchParts(task) {
      return [task.id, task.issue_id, task.issue_key, task.title, task.compact_label]
        .filter(Boolean)
        .map(value => String(value).trim())
        .filter(Boolean);
    }
    function findTaskFromInput(value, fallbackTask = null) {
      const query = String(value || '').trim().toLowerCase();
      if (!query) return fallbackTask;
      const exact = tasks.find(task => taskSearchParts(task).some(part => part.toLowerCase() === query));
      if (exact) return exact;
      return tasks.find(task => taskSearchParts(task).some(part => part.toLowerCase().includes(query))) || null;
    }
    function promptDate(label, fallback) {
      const raw = prompt(label, fallback);
      if (raw === null) return null;
      const value = raw.trim() || fallback;
      const ord = dateOrd(value);
      if (ord === null) {
        alert('日期格式需要是 YYYY-MM-DD。');
        return null;
      }
      return isoFromOrd(ord);
    }
    function normalizeEventType(value, fallback = 'milestone') {
      const normalized = String(value || '').trim().toLowerCase();
      if (!normalized) return fallback;
      if (normalized.includes('求') || normalized.includes('助') || normalized.includes('阻') || normalized.includes('block') || normalized.includes('help')) return 'blocked';
      if (normalized.includes('进') || normalized.includes('中') || normalized.includes('doing') || normalized.includes('progress') || normalized.includes('ongoing')) return 'in_progress';
      if (normalized.includes('完') || normalized.includes('done') || normalized.includes('complete')) return 'completed';
      if (normalized.includes('里') || normalized.includes('碑') || normalized.includes('mile')) return 'milestone';
      return fallback;
    }
    function insertTask(task, parent) {
      if (!parent) {
        tasks.push(task);
        return;
      }
      const childIds = subtreeIds(parent.id);
      const lastChildIndex = Math.max(...tasks.map((item, index) => childIds.has(item.id) ? index : -1));
      const insertAt = Math.max(0, lastChildIndex + 1);
      tasks = [...tasks.slice(0, insertAt), task, ...tasks.slice(insertAt)];
      collapsed.delete(parent.id);
    }
    function addTaskBar() {
      rebuildTaskIndex();
      const rawTitle = prompt('新增任务条名称', '新任务');
      if (rawTitle === null) return;
      const title = rawTitle.trim();
      if (!title) {
        alert('任务名称不能为空。');
        return;
      }
      const rawParent = prompt('父任务（可空；输入任务 KEY / 名称关键字）', '');
      if (rawParent === null) return;
      const parent = findTaskFromInput(rawParent, null);
      if (rawParent.trim() && !parent) {
        alert('没有找到匹配的父任务。');
        return;
      }
      const today = isoFromOrd(todayOrd());
      const startDefault = parent?.start_date || today;
      const targetDefault = parent?.target_date || isoFromOrd((dateOrd(startDefault) ?? todayOrd()) + 6);
      const startDate = promptDate('开始日期 YYYY-MM-DD', startDefault);
      if (!startDate) return;
      const targetDate = promptDate('结束日期 YYYY-MM-DD', targetDefault);
      if (!targetDate) return;
      const startOrd = dateOrd(startDate) ?? todayOrd();
      const targetOrd = dateOrd(targetDate) ?? startOrd;
      const taskId = `local-task:${Date.now()}`;
      const normalizedStart = isoFromOrd(Math.min(startOrd, targetOrd));
      const normalizedTarget = isoFromOrd(Math.max(startOrd, targetOrd));
      const task = {
        id: taskId,
        issue_id: null,
        issue_key: 'NEW',
        title,
        compact_label: compactTaskLabel(title),
        parent_id: parent?.id || null,
        children: [],
        depth: 0,
        order: tasks.length,
        project: parent?.project || '本地新增',
        state: 'draft',
        priority: null,
        progress: 0,
        owner: null,
        color: parent?.color || null,
        labels: ['local'],
        modules: [],
        start_date: normalizedStart,
        target_date: normalizedTarget,
        completed_at: null,
        source_refs: [{ event_time: new Date().toISOString(), event_type: 'local_task_created', source: { table: 'localStorage', id: taskId } }],
        delivery_summary: {
          title,
          next_action: '本地新增任务条，Push changes 后由受控写回流程处理。'
        }
      };
      insertTask(task, parent);
      selectedTaskId = task.id;
      persistEdits();
      rebuildTaskIndex();
      render();
      showTask(task);
    }
    function addEventFromButton() {
      rebuildTaskIndex();
      const fallbackTask = (selectedTaskId && tasksById.get(selectedTaskId)) || visibleTasks()[0] || tasks[0];
      if (!fallbackTask) {
        alert('当前没有任务条。请先新增任务条。');
        return;
      }
      const rawTask = prompt('给哪个任务添加事件？输入任务 KEY / 名称关键字', fallbackTask.issue_key || fallbackTask.title || fallbackTask.id);
      if (rawTask === null) return;
      const task = findTaskFromInput(rawTask, fallbackTask);
      if (!task) {
        alert('没有找到匹配的任务。');
        return;
      }
      const date = promptDate('事件日期 YYYY-MM-DD', isoFromOrd(todayOrd()));
      if (!date) return;
      selectedTaskId = task.id;
      addEventAt(task, date);
    }
    function addEventAt(task, date) {
      const raw = prompt('添加事件类型：求助 / 进行中 / 完成 / 里程碑', '里程碑');
      if (raw === null) return;
      const type = normalizeEventType(raw, 'milestone');
      const summary = prompt('事件简述', eventLabel(type));
      if (summary === null) return;
      const label = summary.trim() || eventLabel(type);
      events.push({
        id: `local:${task.id}:${type}:${date}:${Date.now()}`,
        task_id: task.id,
        type,
        compact_label: compact(label),
        date,
        summary: `${label}: ${task.title}`,
        source_refs: [{ event_time: new Date().toISOString(), event_type: 'local_edit', source: { table: 'localStorage', id: task.id } }]
      });
      persistEdits();
      render();
    }
    function editEvent(event) {
      const rawType = prompt('事件类型：求助 / 进行中 / 完成 / 里程碑', eventLabel(event.type));
      if (rawType === null) return;
      const type = normalizeEventType(rawType, event.type);
      const date = promptDate('事件日期 YYYY-MM-DD', event.date || isoFromOrd(todayOrd()));
      if (!date) return;
      const summary = prompt('事件简述', event.summary || eventLabel(type));
      if (summary === null) return;
      event.type = type;
      event.date = date;
      event.summary = summary.trim() || eventLabel(type);
      event.compact_label = compact(event.summary);
      event.source_refs = event.source_refs || [];
      event.source_refs.push({ event_time: new Date().toISOString(), event_type: 'local_event_edit', source: { table: 'localStorage', id: event.id } });
      persistEdits();
      render();
      showEvent(event);
    }
    function addDemoEvents() {
      const task = visibleTasks()[0] || tasks[0];
      if (!task) return;
      const date = task.start_date || task.target_date || isoFromOrd(todayOrd());
      const stamp = Date.now();
      [
        ['blocked', '求助', '求助: 同日多事件测试'],
        ['in_progress', '进行中', '进行中: 同日多事件测试'],
        ['completed', '完成', '完成: 同日多事件测试'],
        ['milestone', '里程碑', '里程碑: 同日多事件测试']
      ].forEach(([type, label, summary], index) => {
        events.push({
          id: `local-demo:${task.id}:${date}:${stamp}:${index}`,
          task_id: task.id,
          type,
          compact_label: label,
          date,
          summary: `${summary}: ${task.title}`,
          source_refs: [{ event_time: new Date().toISOString(), event_type: 'local_demo', source: { table: 'localStorage', id: task.id } }]
        });
      });
      persistEdits();
      render();
    }
    function deleteTask(task) {
      if (!task || !tasksById.has(task.id)) return;
      if (!confirm(`删除任务「${text(task.title)}」？子任务会保留并上移一层。`)) return;
      const parentId = task.parent_id || null;
      tasks = tasks
        .filter(item => item.id !== task.id)
        .map(item => item.parent_id === task.id ? Object.assign(item, { parent_id: parentId }) : item);
      events = events.filter(event => event.task_id !== task.id);
      if (selectedTaskId === task.id) selectedTaskId = null;
      collapsed.delete(task.id);
      for (const key of [...expandedEventStacks]) {
        if (key.startsWith(`${task.id}:`)) expandedEventStacks.delete(key);
      }
      persistEdits();
      closeDetail();
      render();
    }
    function deleteEvent(event) {
      if (!event) return;
      if (!confirm(`删除事件「${eventLabel(event.type)} · ${text(event.summary)}」？`)) return;
      events = events.filter(item => item.id !== event.id);
      expandedEventStacks.delete(eventStackKey(event.task_id, event.date));
      persistEdits();
      closeDetail();
      render();
    }
    function expandEventStack(key) {
      expandedEventStacks.add(key);
      render();
    }
    function collapseEventStack(key) {
      expandedEventStacks.delete(key);
      render();
    }
    function createMarker(event, stackKey, expandFirst) {
      const marker = document.createElement('button');
      marker.className = `marker ${event.type}`;
      marker.type = 'button';
      marker.title = event.summary;
      marker.setAttribute('aria-label', `${eventLabel(event.type)} · ${text(event.summary)}`);
      const icon = document.createElement('b');
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = symbol[event.type] || '•';
      marker.append(icon);
      marker.addEventListener('click', eventObject => {
        if (shouldSuppressClick(eventObject)) return;
        eventObject.preventDefault();
        eventObject.stopPropagation();
        if (expandFirst && !expandedEventStacks.has(stackKey)) {
          expandEventStack(stackKey);
          return;
        }
        showEvent(event);
      });
      marker.addEventListener('dblclick', eventObject => {
        eventObject.preventDefault();
        eventObject.stopPropagation();
        editEvent(event);
      });
      return marker;
    }
    function moveTask(taskId, drop) {
      if (!drop || !tasksById.has(taskId) || !tasksById.has(drop.targetId)) return;
      const movingIds = subtreeIds(taskId);
      if (movingIds.has(drop.targetId)) return;
      const movingGroup = tasks.filter(task => movingIds.has(task.id));
      const remaining = tasks.filter(task => !movingIds.has(task.id));
      const movingRoot = movingGroup.find(task => task.id === taskId);
      const target = remaining.find(task => task.id === drop.targetId);
      if (!movingRoot || !target) return;
      if (drop.mode === 'child') {
        movingRoot.parent_id = target.id;
        collapsed.delete(target.id);
      } else {
        movingRoot.parent_id = target.parent_id || null;
      }
      const targetIndex = remaining.findIndex(task => task.id === target.id);
      const insertAt = drop.mode === 'before' ? targetIndex : targetIndex + 1;
      tasks = [...remaining.slice(0, insertAt), ...movingGroup, ...remaining.slice(insertAt)];
      rebuildTaskIndex();
      persistEdits();
      render();
    }
    function createGhost(task, event) {
      const ghost = document.createElement('div');
      ghost.className = 'drag-ghost';
      ghost.textContent = `${text(task.issue_key)} ${text(task.compact_label || task.title)}`;
      document.body.append(ghost);
      moveGhost(ghost, event);
      return ghost;
    }
    function moveGhost(ghost, event) {
      ghost.style.transform = `translate(${event.clientX + 12}px, ${event.clientY + 12}px)`;
    }
    function sameDrop(a, b) {
      return !!a === !!b && (!a || (a.mode === b.mode && a.targetId === b.targetId));
    }
    function updateDragDrop(event) {
      if (!dragState) return;
      moveGhost(dragState.ghost, event);
      const element = document.elementFromPoint(event.clientX, event.clientY);
      const row = element?.closest?.('[data-task-id]');
      const targetId = row?.dataset.taskId;
      const moving = subtreeIds(dragState.task.id);
      let nextDrop = null;
      if (targetId && !moving.has(targetId)) {
        const rect = row.getBoundingClientRect();
        const ratio = (event.clientY - rect.top) / Math.max(1, rect.height);
        if (ratio < 0.28) {
          clearTimeout(dragState.hoverTimer);
          dragState.hoverId = null;
          dragState.childReady = false;
          nextDrop = { mode: 'before', targetId };
        } else if (ratio > 0.72) {
          clearTimeout(dragState.hoverTimer);
          dragState.hoverId = null;
          dragState.childReady = false;
          nextDrop = { mode: 'after', targetId };
        }
        else {
          nextDrop = dragState.childReady && dragState.hoverId === targetId ? { mode: 'child', targetId } : { mode: 'after', targetId };
          if (dragState.hoverId !== targetId) {
            clearTimeout(dragState.hoverTimer);
            dragState.hoverId = targetId;
            dragState.childReady = false;
            dragState.hoverTimer = setTimeout(() => {
              if (!dragState || dragState.hoverId !== targetId) return;
              dragState.childReady = true;
              dragState.drop = { mode: 'child', targetId };
              collapsed.delete(targetId);
              render();
            }, 420);
          }
        }
      } else {
        clearTimeout(dragState.hoverTimer);
        dragState.hoverId = null;
        dragState.childReady = false;
      }
      if (!sameDrop(dragState.drop, nextDrop)) {
        dragState.drop = nextDrop;
        render();
      }
    }
    function beginRowDrag(event, task) {
      event.preventDefault();
      clearTimeout(dragState?.hoverTimer);
      dragState = { task, drop: null, hoverId: null, childReady: false, hoverTimer: null, ghost: createGhost(task, event) };
      document.body.classList.add('dragging-row');
      window.addEventListener('pointermove', updateDragDrop);
      window.addEventListener('pointerup', finishRowDrag, { once: true });
      render();
    }
    function finishRowDrag(event) {
      window.removeEventListener('pointermove', updateDragDrop);
      const state = dragState;
      dragState = null;
      document.body.classList.remove('dragging-row');
      clearTimeout(state?.hoverTimer);
      state?.ghost?.remove();
      if (state?.drop) moveTask(state.task.id, state.drop);
      else render();
    }
    function armRowDrag(event, task) {
      if (event.button !== 0) return;
      const startX = event.clientX;
      const startY = event.clientY;
      let started = false;
      const timer = setTimeout(() => {
        started = true;
        cleanup();
        beginRowDrag(event, task);
      }, 360);
      const cleanup = () => {
        clearTimeout(timer);
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', onUp);
      };
      const onMove = moveEvent => {
        if (Math.hypot(moveEvent.clientX - startX, moveEvent.clientY - startY) > 6 && !started) cleanup();
      };
      const onUp = () => cleanup();
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp, { once: true });
    }
    function beginBarResize(event, task, edge) {
      event.preventDefault();
      event.stopPropagation();
      const onMove = moveEvent => {
        setTaskDate(task, edge, ordFromPointer(moveEvent));
        render();
      };
      const onUp = () => {
        window.removeEventListener('pointermove', onMove);
        persistEdits();
      };
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp, { once: true });
    }
    function armEventCreate(event, task) {
      if (event.button !== 0) return;
      if (event.target?.closest?.('.bar-handle')) return;
      const date = isoFromOrd(ordFromPointer(event));
      const timer = setTimeout(() => {
        suppressNextClick = true;
        addEventAt(task, date);
        setTimeout(() => { suppressNextClick = false; }, 500);
      }, 520);
      const cleanup = () => clearTimeout(timer);
      window.addEventListener('pointerup', cleanup, { once: true });
      window.addEventListener('pointermove', cleanup, { once: true });
    }
    function buildRenderItems(baseVisible) {
      const moving = dragState ? subtreeIds(dragState.task.id) : new Set();
      const filtered = baseVisible.filter(task => !moving.has(task.id));
      const items = [];
      for (const task of filtered) {
        if (dragState?.drop?.mode === 'before' && dragState.drop.targetId === task.id) {
          items.push({ kind: 'placeholder', depth: task.depth, mode: 'between' });
        }
        items.push({ kind: 'task', task });
        if (dragState?.drop?.mode === 'after' && dragState.drop.targetId === task.id) {
          items.push({ kind: 'placeholder', depth: task.depth, mode: 'between' });
        }
        if (dragState?.drop?.mode === 'child' && dragState.drop.targetId === task.id) {
          items.push({ kind: 'placeholder', depth: task.depth + 1, mode: 'child' });
        }
      }
      return items;
    }
    function timelineScroller() {
      const pane = document.getElementById('timeline-scroll');
      const paneStyle = pane ? getComputedStyle(pane) : null;
      if (pane && pane.scrollWidth > pane.clientWidth && paneStyle?.overflowX !== 'visible') return pane;
      const layout = document.querySelector('.gantt-layout');
      if (layout && layout.scrollWidth > layout.clientWidth) return layout;
      return pane || document.scrollingElement;
    }
    function timelineContentOffset(scroller) {
      const content = document.getElementById('timeline-content');
      if (!content || !scroller) return 0;
      return content.getBoundingClientRect().left - scroller.getBoundingClientRect().left + scroller.scrollLeft;
    }
    function updateBarLabelPositions() {
      const scroller = timelineScroller();
      if (!scroller) return;
      const contentOffset = timelineContentOffset(scroller);
      const viewportStart = scroller.scrollLeft - contentOffset;
      const viewportEnd = viewportStart + scroller.clientWidth;
      for (const bar of document.querySelectorAll('.bar')) {
        const label = bar.querySelector('.bar-label');
        if (!label) continue;
        const left = Number.parseFloat(bar.style.left) || 0;
        const width = Number.parseFloat(bar.style.width) || bar.offsetWidth || 0;
        const visibleLeft = Math.max(left, viewportStart);
        const visibleRight = Math.min(left + width, viewportEnd);
        const labelWidth = Math.min(label.scrollWidth || 0, Math.max(12, width - 16));
        const minOffset = 8;
        const maxOffset = Math.max(minOffset, width - labelWidth - 8);
        const nextLeft = visibleRight > visibleLeft ? Math.min(Math.max(visibleLeft - left + 8, minOffset), maxOffset) : minOffset;
        label.style.left = `${nextLeft}px`;
        label.style.maxWidth = `${Math.max(12, width - nextLeft - 8)}px`;
      }
    }
    function centerToday() {
      const scroller = timelineScroller();
      if (!scroller) return;
      const today = todayOrd();
      if (today < activeMinOrd || today > activeMaxOrd) return;
      const todayCenter = timelineContentOffset(scroller) + (today - activeMinOrd) * dayWidth() + dayWidth() / 2;
      const target = todayCenter - scroller.clientWidth / 2;
      const maxScroll = Math.max(0, scroller.scrollWidth - scroller.clientWidth);
      scroller.scrollLeft = Math.max(0, Math.min(maxScroll, target));
      updateBarLabelPositions();
    }
    function centerTodayOnce() {
      if (didCenterToday) return;
      didCenterToday = true;
      requestAnimationFrame(() => {
        centerToday();
        setTimeout(centerToday, 80);
        setTimeout(centerToday, 250);
      });
    }
    function render() {
      rebuildTaskIndex();
      updateBounds();
      const visible = visibleTasks();
      const renderItems = buildRenderItems(visible);
      const chartWidth = Math.max(720, (activeMaxOrd - activeMinOrd + 1) * dayWidth());
      const summary = summarize();
      const byTask = eventsByTask();
      document.getElementById('generated').textContent = `Generated ${text(gantt.generated_at)} · ${gantt.sources.timeline_rows} timeline rows · ${gantt.sources.progress_audits} progress audits`;
      document.getElementById('summary').replaceChildren(...[
        `Tasks ${summary.tasks}`,
        `Links ${summary.parent_links}`,
        `Markers ${summary.events}`,
        `Blocked ${summary.blocked}`,
        `In Progress ${summary.in_progress}`,
        `Completed ${summary.completed}`,
        `Milestones ${summary.milestones}`
      ].map(label => {
        const span = document.createElement('span');
        span.textContent = label;
        return span;
      }));
      document.getElementById('empty').hidden = tasks.length > 0;
      const head = document.getElementById('time-head');
      head.style.width = `${chartWidth}px`;
      head.replaceChildren();
      for (let ord = activeMinOrd; ord <= activeMaxOrd; ord += 1) {
        const tick = document.createElement('div');
        const isoDate = isoFromOrd(ord);
        const classes = ['tick'];
        const weekend = isWeekendOrd(ord);
        const holiday = isHolidayDate(isoDate);
        if (weekend) classes.push('weekend');
        if (holiday) classes.push('holiday');
        tick.className = classes.join(' ');
        tick.title = `${isoDate}${holiday ? ' · 节假日' : weekend ? ' · 周末' : ''}`;
        tick.textContent = shortDate(isoDate);
        head.append(tick);
      }
      const taskRows = document.getElementById('task-rows');
      const timelineRows = document.getElementById('timeline-rows');
      taskRows.replaceChildren();
      timelineRows.replaceChildren();
      const metrics = new Map();
      let taskIndex = 0;
      renderItems.forEach((item, index) => {
        if (item.kind === 'placeholder') {
          const row = document.createElement('div');
          row.className = 'task-row placeholder';
          const cell = document.createElement('span');
          cell.className = 'task-main';
          cell.style.paddingLeft = `${28 + item.depth * 14}px`;
          cell.textContent = item.mode === 'child' ? '作为子任务放到这里' : '放到这里';
          row.append(cell, makeCell(''), makeCell(''), makeCell(''));
          taskRows.append(row);
          const track = document.createElement('div');
          track.className = 'timeline-row placeholder';
          track.style.width = `${chartWidth}px`;
          timelineRows.append(track);
          return;
        }
        const task = item.task;
        const isDropParent = dragState?.drop?.mode === 'child' && dragState.drop.targetId === task.id;
        const row = document.createElement('div');
        row.className = `task-row ${isDropParent ? 'drop-parent' : ''}`;
        row.dataset.taskId = task.id;
        const buttonCell = document.createElement('span');
        buttonCell.className = 'task-main';
        const button = document.createElement('button');
        button.className = 'row-button';
        button.type = 'button';
        button.style.paddingLeft = `${4 + task.depth * 14}px`;
        button.title = task.title;
        const chevron = document.createElement('span');
        chevron.className = 'chevron';
        chevron.textContent = task.children && task.children.length ? (collapsed.has(task.id) ? '▸' : '▾') : '•';
        const key = document.createElement('span');
        key.className = 'task-key';
        key.textContent = text(task.issue_key);
        const label = document.createElement('span');
        label.className = 'task-label';
        label.textContent = task.title;
        button.append(chevron, key, label);
        button.addEventListener('click', event => handleTaskRowClick(event, task));
        button.addEventListener('dblclick', event => { event.stopPropagation(); editTaskName(task); });
        button.addEventListener('pointerdown', event => armRowDrag(event, task));
        buttonCell.append(button);
        const ownerCell = makeOwnerCell(task);
        const stateCell = makeCell(stateText(task.state), task.state);
        const rangeCell = makeCell(monthRange(task), `${text(task.start_date)}→${text(task.target_date)}`);
        row.append(buttonCell, ownerCell, stateCell, rangeCell);
        row.addEventListener('click', event => handleTaskRowClick(event, task));
        taskRows.append(row);

        const track = document.createElement('div');
        track.className = `timeline-row ${isDropParent ? 'drop-parent' : ''}`;
        track.dataset.taskId = task.id;
        track.style.width = `${chartWidth}px`;
        const left = offsetForDate(task.start_date);
        const width = widthForTask(task);
        const taskEvents = sortedEvents(byTask.get(task.id) || []);
        const freshnessOpacity = taskFreshnessOpacity(task, byTask);
        metrics.set(task.id, { left, width, y: index * rowHeight() + rowHeight() / 2 });
        const bar = document.createElement('button');
        bar.className = `bar ${task.children && task.children.length ? 'parent' : ''} ${(task.labels || []).includes('blocked') || (task.labels || []).includes('needs-help') ? 'blocked' : ''} ${isDropParent ? 'drop-parent' : ''}`;
        bar.type = 'button';
        bar.style.left = `${left}px`;
        bar.style.width = `${width}px`;
        if (task.color) bar.style.setProperty('--task-color', task.color);
        bar.style.backgroundColor = hexToRgba(taskBaseColor(task), freshnessOpacity);
        const barLabel = document.createElement('span');
        barLabel.className = 'bar-label';
        barLabel.textContent = task.compact_label;
        bar.title = `${task.title} · ${taskStaleTitle(task, byTask)}`;
        const startHandle = document.createElement('span');
        startHandle.className = 'bar-handle start';
        const endHandle = document.createElement('span');
        endHandle.className = 'bar-handle end';
        startHandle.addEventListener('pointerdown', event => beginBarResize(event, task, 'start'));
        endHandle.addEventListener('pointerdown', event => beginBarResize(event, task, 'end'));
        barLabel.addEventListener('dblclick', event => { event.stopPropagation(); editTaskName(task); });
        bar.append(startHandle, barLabel, endHandle);
        bar.addEventListener('click', event => {
          if (shouldSuppressClick(event)) return;
          toggleTask(task);
          showTask(task);
        });
        bar.addEventListener('dblclick', event => { event.stopPropagation(); editTaskName(task); });
        track.append(bar);
        track.addEventListener('pointerdown', event => {
          armEventCreate(event, task);
        });
        const groupedEvents = new Map();
        for (const event of taskEvents) {
          const eventDate = event.date || task.target_date || task.start_date || isoFromOrd(activeMinOrd);
          if (!groupedEvents.has(eventDate)) groupedEvents.set(eventDate, []);
          groupedEvents.get(eventDate).push(event);
        }
        for (const [eventDate, dateEvents] of groupedEvents) {
          const stack = document.createElement('div');
          const stackKey = eventStackKey(task.id, eventDate);
          const isMulti = dateEvents.length > 1;
          const isExpanded = isMulti && expandedEventStacks.has(stackKey);
          stack.className = `event-stack ${isMulti ? 'multi' : ''} ${isMulti ? (isExpanded ? 'expanded' : 'collapsed') : ''}`;
          stack.dataset.stackKey = stackKey;
          stack.style.left = `${offsetForDate(eventDate) + (isMulti && !isExpanded ? 1 : 2)}px`;
          stack.title = `${shortDate(eventDate)} · ${dateEvents.length} event${dateEvents.length > 1 ? 's' : ''}`;
          if (isMulti && !isExpanded) {
            const collapsedWidth = Math.max(16, Math.min(dayWidth() - 2, markerSize() * 1.4));
            const visualSize = Math.max(12, Math.min(markerSize(), collapsedWidth / Math.max(1.4, 1 + (dateEvents.length - 1) * 0.22)));
            const step = dateEvents.length <= 1 ? 0 : (collapsedWidth - visualSize) / (dateEvents.length - 1);
            stack.style.width = `${collapsedWidth}px`;
            stack.style.height = `${Math.max(visualSize + 4, 18)}px`;
            stack.style.setProperty('--stack-marker-size', `${visualSize}px`);
            dateEvents.forEach((event, markerIndex) => {
              const marker = createMarker(event, stackKey, true);
              marker.style.left = `${step * markerIndex}px`;
              marker.style.zIndex = String(markerIndex + 1);
              stack.append(marker);
            });
            stack.addEventListener('click', eventObject => {
              if (shouldSuppressClick(eventObject)) return;
              eventObject.preventDefault();
              eventObject.stopPropagation();
              expandEventStack(stackKey);
            });
          } else {
            stack.style.removeProperty('--stack-marker-size');
            if (isMulti) {
              const collapse = document.createElement('button');
              collapse.className = 'stack-collapse';
              collapse.type = 'button';
              collapse.title = '折叠';
              collapse.setAttribute('aria-label', '折叠同日事件');
              collapse.textContent = '‹';
              collapse.addEventListener('click', eventObject => {
                eventObject.preventDefault();
                eventObject.stopPropagation();
                collapseEventStack(stackKey);
              });
              stack.append(collapse);
            }
            for (const event of dateEvents) stack.append(createMarker(event, stackKey, false));
          }
          track.append(stack);
        }
        timelineRows.append(track);
        taskIndex += 1;
      });
      const connectorLayer = document.getElementById('connector-layer');
      connectorLayer.setAttribute('width', chartWidth);
      connectorLayer.setAttribute('height', Math.max(renderItems.length * rowHeight(), 1));
      connectorLayer.style.width = `${chartWidth}px`;
      connectorLayer.style.height = `${Math.max(renderItems.length * rowHeight(), 1)}px`;
      connectorLayer.replaceChildren();
      const visibleIds = new Set(visible.map(task => task.id));
      const childrenByParent = new Map();
      for (const task of visible) {
        if (!task.parent_id || !visibleIds.has(task.parent_id)) continue;
        if (!childrenByParent.has(task.parent_id)) childrenByParent.set(task.parent_id, []);
        childrenByParent.get(task.parent_id).push(task);
      }
      for (const [parentId, children] of childrenByParent) {
        const parentMetric = metrics.get(parentId);
        if (!parentMetric) continue;
        const parentX = parentMetric.left + 10;
        const parentY = parentMetric.y;
        const childMetrics = children
          .map(child => ({ child, metric: metrics.get(child.id) }))
          .filter(item => item.metric)
          .sort((a, b) => a.metric.y - b.metric.y);
        if (!childMetrics.length) continue;
        const trunkX = Math.min(parentX + 22, ...childMetrics.map(item => item.metric.left + 8));
        const parts = [`M ${parentX} ${parentY} H ${trunkX}`];
        for (const item of childMetrics) {
          const childX = item.metric.left + 8;
          const childY = item.metric.y;
          parts.push(`V ${childY} H ${childX}`);
          parts.push(`M ${trunkX} ${childY}`);
        }
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('class', 'connector');
        path.setAttribute('d', parts.join(' '));
        connectorLayer.append(path);
      }
      updateBarLabelPositions();
      centerTodayOnce();
    }
    document.getElementById('density-dense').addEventListener('click', () => setDensity('dense'));
    document.getElementById('density-present').addEventListener('click', () => setDensity('present'));
    document.getElementById('expand-all').addEventListener('click', () => { collapsed.clear(); render(); });
    document.getElementById('collapse-all').addEventListener('click', () => {
      collapsed.clear();
      for (const task of tasks) if (task.children && task.children.length) collapsed.add(task.id);
      render();
    });
    document.getElementById('refresh').addEventListener('click', () => location.reload());
    document.getElementById('push-edits').addEventListener('click', pushEdits);
    document.getElementById('export-report').addEventListener('click', exportReport);
    document.getElementById('add-task').addEventListener('click', addTaskBar);
    document.getElementById('add-event').addEventListener('click', addEventFromButton);
    document.getElementById('marker-demo').addEventListener('click', addDemoEvents);
    document.getElementById('reset-edits').addEventListener('click', () => {
      if (!confirm('清除本页本地修改？不会影响 Plane 数据。')) return;
      localStorage.removeItem(STORAGE_KEY);
      tasks = clone(gantt.tasks);
      events = clone(gantt.events);
      selectedTaskId = null;
      collapsed.clear();
      render();
    });
    document.getElementById('detail-close').addEventListener('click', () => {
      closeDetail();
    });
    document.getElementById('timeline-scroll').addEventListener('scroll', updateBarLabelPositions);
    document.querySelector('.gantt-layout').addEventListener('scroll', updateBarLabelPositions);
    window.addEventListener('resize', render);
    render();
  </script>
</body>
</html>
""".replace("__DATA__", data_json)
    path.write_text(html_text, encoding="utf-8")
    return path


def project_html(project: dict[str, Any]) -> str:
    state_total = sum(project["state_counts"].values()) or 1
    bars = "".join(
        f"<span class='bar' style='width:{max(30, int(count / state_total * 120))}px'>{esc(state)} {count}</span>"
        for state, count in project["state_counts"].items()
    ) or "<span class='badge'>no issues</span>"
    people = "".join(f"<span class='badge b-green'>{esc(name)} {count}</span>" for name, count in project["people"].items()) or "<span class='badge'>unknown owner</span>"
    risks = []
    if project["blockers"]:
        risks.append(f"<span class='badge b-red'>blockers {len(project['blockers'])}</span>")
    if project["unresolved"]:
        risks.append(f"<span class='badge b-amber'>unresolved {len(project['unresolved'])}</span>")
    if project["stale_issues"]:
        risks.append(f"<span class='badge b-amber'>stale {len(project['stale_issues'])}</span>")
    risk_text = "".join(risks) or "<span class='badge b-green'>no active risk</span>"
    issue_items = "".join(
        f"<li>{esc(issue.get('issue_key'))} {esc(issue.get('issue_title'))} <span class='muted'>{esc(issue.get('state'))}</span></li>"
        for issue in project["issues"][:6]
    ) or "<li class='muted'>No Plane issues in source window</li>"
    actions = "".join(f"<li>{esc(action)}</li>" for action in project["next_actions"])
    return f"""
<article class="project">
  <h3>{esc(project['project'])}</h3>
  <div class="bars">{bars}</div>
  <p>{people}</p>
  <p>{risk_text}</p>
  <div class="muted">Next review: {esc(project['next_review_date'])}</div>
  <ul>{issue_items}</ul>
  <ul>{actions}</ul>
</article>
"""


def write_markdown(data: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "delivery-plan.md"
    lines = [
        "# Delivery Plan",
        "",
        f"Generated: {data['generated_at']}",
        "",
        "## Summary",
        "",
    ]
    for key, value in data["summary"].items():
        lines.append(f"- {key}: {value}")
    for project in data["projects"]:
        lines.extend(["", f"## Project: {project['project']}", ""])
        lines.append(f"- Next review date: {project['next_review_date']}")
        lines.append(f"- People: {', '.join(project['people'].keys()) or 'unknown'}")
        lines.append(f"- State counts: {dict(project['state_counts'])}")
        lines.append("")
        lines.append("### Work Items")
        if project["issues"]:
            for issue in project["issues"]:
                lines.append(f"- {issue.get('issue_key')} {issue.get('issue_title')} [{issue.get('state') or 'unknown'}]")
        else:
            lines.append("- No Plane issues in source window")
        lines.append("")
        lines.append("### Risks And Blockers")
        if project["blockers"] or project["unresolved"] or project["stale_issues"]:
            for blocker in project["blockers"]:
                lines.append(f"- Blocker: {blocker.get('person')} / {blocker.get('work_item')} / {blocker.get('blocker')}")
            for item in project["unresolved"]:
                lines.append(f"- Unresolved draft: {item.get('body')} ({item.get('reason')})")
            for issue in project["stale_issues"]:
                lines.append(f"- Stale: {issue.get('issue_key')} {issue.get('issue_title')}")
        else:
            lines.append("- No active risks detected")
        lines.append("")
        lines.append("### Next Actions")
        for action in project["next_actions"]:
            lines.append(f"- {action}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local delivery dashboard from Plane and progress artifacts.")
    parser.add_argument("--timeline", default=str(ROOT_DIR / "exports/plane/timeline.jsonl"))
    parser.add_argument("--progress-dir", default=str(ROOT_DIR / "exports/progress"))
    parser.add_argument("--output-dir", default=str(ROOT_DIR / "exports/delivery"))
    parser.add_argument("--stale-days", type=int, default=7)
    args = parser.parse_args()

    timeline_path = Path(args.timeline)
    progress_dir = Path(args.progress_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timeline = load_jsonl(timeline_path)
    audits = load_progress_audits(progress_dir)

    dashboard = build_dashboard(timeline, audits, args.stale_days)
    gantt = build_gantt_data(timeline, audits)
    json_path = write_json(dashboard, output_dir)
    html_path = write_html(dashboard, output_dir)
    md_path = write_markdown(dashboard, output_dir)
    gantt_json_path = write_gantt_json(gantt, output_dir)
    gantt_html_path = write_gantt_html(gantt, output_dir)

    print(f"Wrote {json_path}")
    print(f"Wrote {html_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {gantt_json_path}")
    print(f"Wrote {gantt_html_path}")
    print(json.dumps(dashboard["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
