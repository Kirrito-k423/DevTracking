#!/usr/bin/env python3
"""Apply structured daily progress events to the local Plane project.

Input is intentionally structured JSON. The agent/skill is responsible for
turning natural language into event specs; this script only performs a
repeatable, idempotent Plane write through Plane's Django model layer.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT_DIR / "plane-selfhost/plane-app/docker-compose.yaml"
ENV_FILE = ROOT_DIR / "plane-selfhost/plane-app/plane.env"

DEFAULT_WORKSPACE = "teamwork"
DEFAULT_PROJECT_ID = "e4924234-5afd-4954-989d-ac094fe75976"
DEFAULT_OVERVIEW_VIEW_ID = "070f9a9d-21b7-4f8c-b21d-21c04d843366"
DEFAULT_SFT_ISSUE_ID = "534f110e-1401-4546-b84f-aeeec0008cb1"
DEFAULT_CHUNKMOE_ISSUE_ID = "c83d2690-d6c1-4839-9d25-b45043a1387d"


DJANGO_SCRIPT = r"""
import html
import json
import uuid
from django.db.models import Max
from plane.db.models import (
    Workspace, Project, User, IssueView, Issue, Label, IssueLabel,
    Module, ModuleIssue, State,
)

event_specs = json.loads({event_specs_json!r})
workspace = Workspace.objects.get(slug={workspace_slug!r})
project = Project.objects.get(id={project_id!r})
owner_email = {owner_email!r}
overview_for_owner = IssueView.objects.filter(id={overview_view_id!r}).first()
owner = None
if owner_email:
    owner = User.objects.get(email=owner_email)
for candidate in [
    getattr(overview_for_owner, 'owned_by', None),
    getattr(project, 'created_by', None),
    getattr(project, 'updated_by', None),
    getattr(workspace, 'created_by', None),
    getattr(workspace, 'updated_by', None),
]:
    if owner is None and candidate is not None:
        owner = candidate
if owner is None:
    owner = User.objects.filter(is_active=True).order_by('created_at').first() or User.objects.order_by('created_at').first()
if owner is None:
    raise RuntimeError('Could not infer a Plane user for created_by/updated_by fields.')

standard_labels = {{
    'blocked': ('#EF4444', '关键阻塞：影响交付、需要跟进解除。'),
    'needs-help': ('#F97316', '需要协助：需要他人介入或确认资源。'),
    'milestone': ('#2563EB', '关键达成节点：阶段交付、验收点、里程碑。'),
    'breakthrough': ('#16A34A', '关键突破：技术、性能、流程上有实质突破。'),
    'daily-event': ('#64748B', '每日事件：用于把口头日报落到 Plane view。'),
    'owner:于家硕': ('#A855F7', '临时人员标记：于家硕。正式成员接入后可替换为 assignee。'),
    'owner:侯玉峰': ('#0EA5E9', '临时人员标记：侯玉峰。正式成员接入后可替换为 assignee。'),
}}
standard_modules = {{
    'SFT 交付': ('InternS2 SFT 交付主线。', 'in-progress'),
    'chunkmoe': ('chunkmoe 性能优化与相关实现。', 'in-progress'),
    '评测': ('评测、验收与效果回归。', 'backlog'),
}}


def get_label(name):
    color, description = standard_labels.get(name, ('#64748B', f'由日报写入流程创建：{{name}}'))
    label, _ = Label.objects.get_or_create(
        workspace=workspace,
        project=project,
        name=name,
        defaults={{
            'color': color,
            'description': description,
            'created_by': owner,
            'updated_by': owner,
            'external_source': 'codex-plane-daily-record',
            'external_id': f'label:{{name}}',
        }},
    )
    if label.deleted_at is not None:
        label.deleted_at = None
        label.updated_by = owner
        label.save(update_fields=['deleted_at', 'updated_by', 'updated_at'])
    return label


def get_module(name):
    description, status = standard_modules.get(name, (f'由日报写入流程创建：{{name}}', 'backlog'))
    module, _ = Module.objects.get_or_create(
        workspace=workspace,
        project=project,
        name=name,
        defaults={{
            'description': description,
            'status': status,
            'lead': owner,
            'created_by': owner,
            'updated_by': owner,
            'external_source': 'codex-plane-daily-record',
            'external_id': f'module:{{name}}',
        }},
    )
    if module.deleted_at is not None or module.archived_at is not None:
        module.deleted_at = None
        module.archived_at = None
        module.updated_by = owner
        module.save(update_fields=['deleted_at', 'archived_at', 'updated_by', 'updated_at'])
    return module


state_by_group = {{
    state.group: state
    for state in State.objects.filter(workspace=workspace, project=project, deleted_at__isnull=True)
}}
state_by_name = {{
    state.name.lower(): state
    for state in State.objects.filter(workspace=workspace, project=project, deleted_at__isnull=True)
}}
state_aliases = {{
    'backlog': 'backlog',
    'todo': 'unstarted',
    'blocked': 'unstarted',
    'in_progress': 'started',
    'started': 'started',
    'done': 'completed',
    'completed': 'completed',
    'cancelled': 'cancelled',
}}
parent_aliases = {{
    'sft': {sft_issue_id!r},
    'interns2-sft': {sft_issue_id!r},
    'interns2 sft': {sft_issue_id!r},
    'chunkmoe': {chunkmoe_issue_id!r},
    'chunk-moe': {chunkmoe_issue_id!r},
    'chunk moe': {chunkmoe_issue_id!r},
}}


def get_state(value):
    if not value:
        return state_by_group.get('started')
    normalized = str(value).strip().lower().replace('-', '_').replace(' ', '_')
    group = state_aliases.get(normalized, normalized)
    return state_by_group.get(group) or state_by_name.get(str(value).strip().lower())


def next_sequence_id():
    current = Issue.all_objects.filter(project=project).aggregate(max_seq=Max('sequence_id'))['max_seq'] or 0
    return current + 1


def resolve_parent(value):
    if not value:
        return None
    raw = str(value).strip()
    alias = raw.lower()
    if alias in parent_aliases:
        return Issue.all_objects.get(id=parent_aliases[alias])
    try:
        return Issue.all_objects.get(workspace=workspace, project=project, id=uuid.UUID(raw))
    except Exception:
        pass
    if '-' in raw:
        maybe_seq = raw.split('-')[-1]
    else:
        maybe_seq = raw
    if maybe_seq.isdigit():
        return Issue.all_objects.filter(workspace=workspace, project=project, sequence_id=int(maybe_seq)).first()
    return Issue.all_objects.filter(workspace=workspace, project=project, name__icontains=raw).order_by('sequence_id').first()


def upsert_issue(spec):
    external_id = spec['external_id']
    issue = Issue.all_objects.filter(
        workspace=workspace,
        project=project,
        external_source='codex-daily-record',
        external_id=external_id,
    ).first()
    if issue is None:
        issue = Issue(
            workspace=workspace,
            project=project,
            sequence_id=next_sequence_id(),
            created_by=owner,
            updated_by=owner,
            external_source='codex-daily-record',
            external_id=external_id,
        )
    description = spec.get('description') or ''
    issue.name = spec['title']
    issue.description_html = f"<p>{{html.escape(description)}}</p>" if description else '<p></p>'
    issue.description_stripped = description
    issue.priority = spec.get('priority') or 'none'
    issue.start_date = spec.get('start_date')
    issue.target_date = spec.get('target_date')
    issue.parent = resolve_parent(spec.get('parent'))
    issue.state = get_state(spec.get('state')) or state_by_group.get('started')
    issue.deleted_at = None
    issue.is_draft = False
    issue.updated_by = owner
    issue.save()

    for label_name in spec.get('labels', []):
        label = get_label(label_name)
        bridge, _ = IssueLabel.objects.get_or_create(
            workspace=workspace,
            project=project,
            issue=issue,
            label=label,
            defaults={{'created_by': owner, 'updated_by': owner}},
        )
        if bridge.deleted_at is not None:
            bridge.deleted_at = None
            bridge.updated_by = owner
            bridge.save(update_fields=['deleted_at', 'updated_by', 'updated_at'])

    for module_name in spec.get('modules', []):
        module = get_module(module_name)
        bridge, _ = ModuleIssue.objects.get_or_create(
            workspace=workspace,
            project=project,
            issue=issue,
            module=module,
            defaults={{'created_by': owner, 'updated_by': owner}},
        )
        if bridge.deleted_at is not None:
            bridge.deleted_at = None
            bridge.updated_by = owner
            bridge.save(update_fields=['deleted_at', 'updated_by', 'updated_at'])

    labels = list(
        IssueLabel.objects.filter(issue=issue, deleted_at__isnull=True)
        .select_related('label')
        .order_by('label__name')
        .values_list('label__name', flat=True)
    )
    modules = list(
        ModuleIssue.objects.filter(issue=issue, deleted_at__isnull=True)
        .select_related('module')
        .order_by('module__name')
        .values_list('module__name', flat=True)
    )
    return {{
        'issue_id': str(issue.id),
        'issue_key': f'{{project.identifier}}-{{issue.sequence_id}}',
        'title': issue.name,
        'state': issue.state.name if issue.state else None,
        'priority': issue.priority,
        'parent_id': str(issue.parent_id) if issue.parent_id else None,
        'labels': labels,
        'modules': modules,
        'start_date': str(issue.start_date) if issue.start_date else None,
        'target_date': str(issue.target_date) if issue.target_date else None,
        'external_id': issue.external_id,
    }}


results = [upsert_issue(spec) for spec in event_specs]
print(json.dumps({{'applied': results}}, ensure_ascii=False, indent=2, sort_keys=True))
"""


def today_shanghai() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def load_events(args: argparse.Namespace) -> list[dict]:
    if args.events_json:
        return json.loads(args.events_json)
    if args.events_file:
        return json.loads(Path(args.events_file).read_text(encoding="utf-8"))
    raise SystemExit("Provide --events-json or --events-file.")


def infer_person(event: dict) -> str | None:
    if event.get("person"):
        return event["person"]
    for label in event.get("labels", []):
        if str(label).startswith("owner:"):
            return str(label).split(":", 1)[1]
    return None


def infer_status(event: dict) -> str:
    labels = set(event.get("labels", []))
    state = str(event.get("state") or "").lower()
    if "blocked" in labels:
        return "waiting"
    if state in {"done", "completed"}:
        return "completed"
    if state in {"todo", "blocked"}:
        return "waiting" if "needs-help" in labels else "reported"
    if state in {"in_progress", "started"}:
        return "in_progress"
    return "reported"


def infer_blocker(event: dict) -> str | None:
    if event.get("blocker"):
        return event["blocker"]
    labels = set(event.get("labels", []))
    if "blocked" not in labels and "needs-help" not in labels:
        return None
    description = event.get("description") or event.get("title") or ""
    for marker in ("卡住", "阻塞", "等待", "排队"):
        if marker in description:
            return marker
    return "需要协助"


def write_progress_audit(
    events: list[dict],
    source_id: str,
    raw_text: str | None,
    generated_at: str,
    audit_dir: Path,
) -> Path:
    audit_events = []
    for index, event in enumerate(events, start=1):
        labels = set(event.get("labels", []))
        audit_events.append(
            {
                "event_id": event["external_id"],
                "event_time": generated_at,
                "person": infer_person(event),
                "project": event.get("project") or "浦江项目",
                "project_aliases": ["浦江项目", "浦江"],
                "raw_text": event.get("raw_text") or event.get("description") or event.get("title"),
                "work_item": event.get("work_item") or event.get("title"),
                "status": infer_status(event),
                "blocker": infer_blocker(event),
                "source": {
                    "type": "user_progress_message",
                    "source_id": source_id,
                    "segment_index": index,
                },
                "resolution": {
                    "project": {"status": "resolved", "project": {"project": "浦江"}},
                    "issue": {"status": "applied", "issue": {"external_id": event["external_id"]}},
                },
                "labels": sorted(labels),
                "modules": event.get("modules", []),
            }
        )
    audit = {
        "mode": "apply",
        "source_id": source_id,
        "generated_at": generated_at,
        "input": raw_text or "；".join(event.get("raw_text") or event.get("description") or event["title"] for event in events),
        "events": audit_events,
        "planned_plane_changes": [],
        "applied_changes": [{"operation": "plane_daily_record_upsert", "count": len(events)}],
        "warnings": [],
        "write_boundary": "Plane daily record applied through controlled local connector; do not mutate Plane PostgreSQL with ad hoc SQL.",
    }
    audit_dir.mkdir(parents=True, exist_ok=True)
    path = audit_dir / f"{source_id}.json"
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply structured daily records to Plane.")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE)
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--owner-email", default=os.environ.get("PLANE_DAILY_OWNER_EMAIL"))
    parser.add_argument("--overview-view-id", default=DEFAULT_OVERVIEW_VIEW_ID)
    parser.add_argument("--sft-issue-id", default=DEFAULT_SFT_ISSUE_ID)
    parser.add_argument("--chunkmoe-issue-id", default=DEFAULT_CHUNKMOE_ISSUE_ID)
    parser.add_argument("--date", default=today_shanghai())
    parser.add_argument("--source-id", default=None)
    parser.add_argument("--events-json")
    parser.add_argument("--events-file")
    parser.add_argument("--raw-text", help="Original user daily record text, stored in progress audit.")
    parser.add_argument("--audit-dir", default=str(ROOT_DIR / "exports/progress"))
    parser.add_argument("--skip-bootstrap", action="store_true")
    args = parser.parse_args()

    events = load_events(args)
    source_id = args.source_id or f"daily-{args.date.replace('-', '')}"
    for index, event in enumerate(events, start=1):
        event.setdefault("start_date", args.date)
        event.setdefault("target_date", args.date)
        event["external_id"] = f"{source_id}:{event.get('external_id') or f'segment:{index}'}"

    generated_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()

    if not args.skip_bootstrap:
        subprocess.run([str(ROOT_DIR / "scripts/bootstrap-plane-visual-constructs.py")], cwd=ROOT_DIR, check=True)

    script = DJANGO_SCRIPT.format(
        event_specs_json=json.dumps(events, ensure_ascii=False),
        workspace_slug=args.workspace,
        project_id=args.project_id,
        owner_email=args.owner_email,
        overview_view_id=args.overview_view_id,
        sft_issue_id=args.sft_issue_id,
        chunkmoe_issue_id=args.chunkmoe_issue_id,
    )
    command = [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "--env-file",
        str(ENV_FILE),
        "exec",
        "-T",
        "api",
        "python",
        "manage.py",
        "shell",
    ]
    completed = subprocess.run(command, input=script, text=True, cwd=ROOT_DIR, check=False, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode == 0:
        audit_path = write_progress_audit(
            events=events,
            source_id=source_id,
            raw_text=args.raw_text,
            generated_at=generated_at,
            audit_dir=Path(args.audit_dir),
        )
        print(f"Wrote progress audit: {audit_path}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
