#!/usr/bin/env python3
"""Build a static delivery dashboard from Plane timeline and progress audits."""

from __future__ import annotations

import argparse
import html
import json
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


def write_json(data: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "dashboard.json"
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

    dashboard = build_dashboard(load_jsonl(timeline_path), load_progress_audits(progress_dir), args.stale_days)
    json_path = write_json(dashboard, output_dir)
    html_path = write_html(dashboard, output_dir)
    md_path = write_markdown(dashboard, output_dir)

    print(f"Wrote {json_path}")
    print(f"Wrote {html_path}")
    print(f"Wrote {md_path}")
    print(json.dumps(dashboard["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
