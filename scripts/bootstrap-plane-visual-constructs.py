#!/usr/bin/env python3
"""Create the Plane visual constructs used by the delivery workflow.

This script is intentionally idempotent. It creates or updates:

- Labels for blockers, help requests, milestones, breakthroughs, daily events,
  and temporary owner markers.
- Project modules for SFT delivery, chunkmoe, and evaluation.
- Project views for delivery overview, key blockers, key nodes, and daily events.
- The current seed relationships for InternS2 SFT and chunkmoe.

It runs through the Plane backend container so it uses Plane's Django models
instead of writing SQL directly.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import textwrap
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT_DIR / "plane-selfhost/plane-app/docker-compose.yaml"
ENV_FILE = ROOT_DIR / "plane-selfhost/plane-app/plane.env"

DEFAULT_WORKSPACE = "teamwork"
DEFAULT_PROJECT_ID = "e4924234-5afd-4954-989d-ac094fe75976"
DEFAULT_OVERVIEW_VIEW_ID = "070f9a9d-21b7-4f8c-b21d-21c04d843366"
DEFAULT_SFT_ISSUE_ID = "534f110e-1401-4546-b84f-aeeec0008cb1"
DEFAULT_CHUNKMOE_ISSUE_ID = "c83d2690-d6c1-4839-9d25-b45043a1387d"


DJANGO_SCRIPT = r"""
from plane.db.models import (
    Workspace, Project, User, Label, IssueView, Issue, IssueLabel,
    Module, ModuleIssue, State,
)
from django.db.models import Max
from plane.utils.filters import LegacyToRichFiltersConverter

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

label_specs = [
    ('blocked', '#EF4444', '关键阻塞：影响交付、需要跟进解除。'),
    ('needs-help', '#F97316', '需要协助：需要他人介入或确认资源。'),
    ('milestone', '#2563EB', '关键达成节点：阶段交付、验收点、里程碑。'),
    ('breakthrough', '#16A34A', '关键突破：技术、性能、流程上有实质突破。'),
    ('daily-event', '#64748B', '每日事件：用于把口头日报落到 Plane view。'),
    ('owner:于家硕', '#A855F7', '临时人员标记：于家硕。正式成员接入后可替换为 assignee。'),
    ('owner:侯玉峰', '#0EA5E9', '临时人员标记：侯玉峰。正式成员接入后可替换为 assignee。'),
]
labels = {{}}
for name, color, description in label_specs:
    label, _ = Label.objects.get_or_create(
        workspace=workspace,
        project=project,
        name=name,
        defaults={{
            'color': color,
            'description': description,
            'created_by': owner,
            'updated_by': owner,
            'external_source': 'codex-plane-constructs',
            'external_id': f'label:{{name}}',
        }},
    )
    updates = []
    for field, value in [('color', color), ('description', description)]:
        if getattr(label, field) != value:
            setattr(label, field, value)
            updates.append(field)
    if label.deleted_at is not None:
        label.deleted_at = None
        updates.append('deleted_at')
    if updates:
        label.updated_by = owner
        updates.extend(['updated_by', 'updated_at'])
        label.save(update_fields=list(dict.fromkeys(updates)))
    labels[name] = label

module_specs = [
    ('SFT 交付', 'InternS2 SFT 交付主线。', '2026-06-01', '2026-07-15', 'in-progress'),
    ('chunkmoe', 'chunkmoe 性能优化与相关实现。', '2026-07-03', '2026-07-15', 'in-progress'),
    ('评测', '评测、验收与效果回归。', None, None, 'backlog'),
]
modules = {{}}
for name, description, start_date, target_date, status in module_specs:
    module, _ = Module.objects.get_or_create(
        workspace=workspace,
        project=project,
        name=name,
        defaults={{
            'description': description,
            'start_date': start_date,
            'target_date': target_date,
            'status': status,
            'lead': owner,
            'created_by': owner,
            'updated_by': owner,
            'external_source': 'codex-plane-constructs',
            'external_id': f'module:{{name}}',
        }},
    )
    updates = []
    for field, value in [
        ('description', description),
        ('start_date', start_date),
        ('target_date', target_date),
        ('status', status),
    ]:
        if getattr(module, field) != value:
            setattr(module, field, value)
            updates.append(field)
    if module.archived_at is not None:
        module.archived_at = None
        updates.append('archived_at')
    if module.deleted_at is not None:
        module.deleted_at = None
        updates.append('deleted_at')
    if updates:
        module.updated_by = owner
        updates.extend(['updated_by', 'updated_at'])
        module.save(update_fields=list(dict.fromkeys(updates)))
    modules[name] = module

sft = Issue.all_objects.get(id={sft_issue_id!r})
chunk = Issue.all_objects.get(id={chunkmoe_issue_id!r})
if chunk.deleted_at is not None:
    chunk.deleted_at = None
if chunk.parent_id != sft.id:
    chunk.parent = sft
chunk.save(update_fields=['deleted_at', 'parent', 'updated_at'])

state_by_group = {{
    state.group: state
    for state in State.objects.filter(workspace=workspace, project=project, deleted_at__isnull=True)
}}
state_by_name = {{
    state.name.lower(): state
    for state in State.objects.filter(workspace=workspace, project=project, deleted_at__isnull=True)
}}


def next_sequence_id():
    current = Issue.all_objects.filter(project=project).aggregate(max_seq=Max('sequence_id'))['max_seq'] or 0
    return current + 1


def upsert_seed_issue(spec):
    issue = Issue.all_objects.filter(
        workspace=workspace,
        project=project,
        external_source='codex-progress-event',
        external_id=spec['external_id'],
    ).first()
    create = issue is None
    state = state_by_group.get(spec['state_group']) or state_by_name.get(spec['state_name'].lower())
    if create:
        issue = Issue(
            workspace=workspace,
            project=project,
            sequence_id=next_sequence_id(),
            created_by=owner,
            updated_by=owner,
            external_source='codex-progress-event',
            external_id=spec['external_id'],
        )
    issue.name = spec['name']
    issue.description_html = f"<p>{{spec['description']}}</p>"
    issue.description_stripped = spec['description']
    issue.priority = spec['priority']
    issue.start_date = spec['start_date']
    issue.target_date = spec['target_date']
    issue.parent = spec['parent']
    issue.state = state
    issue.deleted_at = None
    issue.is_draft = False
    issue.updated_by = owner
    issue.save()
    return issue


event_issue_specs = [
    {{
        'external_id': 'smoke-final-20260702:segment:1',
        'name': '2026-07-02 侯玉峰：开发 chunkmoe',
        'description': '日报事件：侯玉峰，浦江项目，开发 chunkmoe。来源 smoke-final-20260702:segment:1。',
        'priority': 'medium',
        'start_date': '2026-07-02',
        'target_date': '2026-07-02',
        'parent': chunk,
        'state_group': 'started',
        'state_name': 'In Progress',
        'labels': ['daily-event', 'breakthrough', 'owner:侯玉峰'],
        'modules': ['SFT 交付', 'chunkmoe'],
    }},
    {{
        'external_id': 'smoke-final-20260702:segment:2',
        'name': '2026-07-02 于家硕：SFT 排队等待资源',
        'description': '日报事件与关键阻塞：于家硕，浦江项目，SFT 任务排队一天。来源 smoke-final-20260702:segment:2。',
        'priority': 'high',
        'start_date': '2026-07-02',
        'target_date': '2026-07-03',
        'parent': sft,
        'state_group': 'unstarted',
        'state_name': 'Todo',
        'labels': ['daily-event', 'blocked', 'needs-help', 'owner:于家硕'],
        'modules': ['SFT 交付'],
    }},
]
event_issues = [upsert_seed_issue(spec) for spec in event_issue_specs]

issue_label_map = {{
    sft: ['milestone', 'owner:于家硕'],
    chunk: ['breakthrough', 'owner:侯玉峰'],
}}
for spec, issue in zip(event_issue_specs, event_issues):
    issue_label_map[issue] = spec['labels']
for issue, names in issue_label_map.items():
    for name in names:
        bridge, _ = IssueLabel.objects.get_or_create(
            workspace=workspace,
            project=project,
            issue=issue,
            label=labels[name],
            defaults={{'created_by': owner, 'updated_by': owner}},
        )
        if bridge.deleted_at is not None:
            bridge.deleted_at = None
            bridge.updated_by = owner
            bridge.save(update_fields=['deleted_at', 'updated_by', 'updated_at'])

module_issue_map = {{
    modules['SFT 交付']: [sft, chunk],
    modules['chunkmoe']: [chunk],
}}
for spec, issue in zip(event_issue_specs, event_issues):
    for module_name in spec['modules']:
        module_issue_map.setdefault(modules[module_name], []).append(issue)
for module, issues in module_issue_map.items():
    for issue in issues:
        bridge, _ = ModuleIssue.objects.get_or_create(
            workspace=workspace,
            project=project,
            module=module,
            issue=issue,
            defaults={{'created_by': owner, 'updated_by': owner}},
        )
        if bridge.deleted_at is not None:
            bridge.deleted_at = None
            bridge.updated_by = owner
            bridge.save(update_fields=['deleted_at', 'updated_by', 'updated_at'])

base_display_properties = {{
    'key': True,
    'link': True,
    'cycle': True,
    'state': True,
    'labels': True,
    'modules': True,
    'assignee': True,
    'due_date': True,
    'estimate': True,
    'priority': True,
    'created_on': True,
    'issue_type': True,
    'start_date': True,
    'updated_on': True,
    'sub_issue_count': True,
    'attachment_count': True,
}}
rich_filter_converter = LegacyToRichFiltersConverter()
view_specs = [
    {{
        'name': '交付总览',
        'description': '甘特视图：展示交付物、子任务、关键节点和关键突破。',
        'filters': {{'sub_issue': 'true'}},
        'display_filters': {{
            'layout': 'gantt_chart',
            'calendar': {{'layout': 'month', 'show_weekends': False}},
            'group_by': 'state',
            'order_by': 'sort_order',
            'sub_issue': True,
            'sub_group_by': None,
            'show_empty_groups': False,
        }},
    }},
    {{
        'name': '关键阻塞',
        'description': '只看 blocked / needs-help，用于每天拉通求助。',
        'filters': {{'labels': [str(labels['blocked'].id), str(labels['needs-help'].id)], 'sub_issue': 'true'}},
        'display_filters': {{
            'layout': 'kanban',
            'group_by': 'state',
            'order_by': 'priority',
            'sub_issue': True,
            'sub_group_by': None,
            'show_empty_groups': True,
            'calendar_date_range': '',
        }},
    }},
    {{
        'name': '关键节点',
        'description': '只看 milestone / breakthrough，用于展示关键达成和突破。',
        'filters': {{'labels': [str(labels['milestone'].id), str(labels['breakthrough'].id)], 'sub_issue': 'true'}},
        'display_filters': {{
            'layout': 'gantt_chart',
            'calendar': {{'layout': 'month', 'show_weekends': False}},
            'group_by': 'state',
            'order_by': 'sort_order',
            'sub_issue': True,
            'sub_group_by': None,
            'show_empty_groups': False,
        }},
    }},
    {{
        'name': '每日事件',
        'description': '只看 daily-event，用于沉淀每日进展，不污染主交付视图。',
        'filters': {{'labels': [str(labels['daily-event'].id)], 'sub_issue': 'true'}},
        'display_filters': {{
            'layout': 'list',
            'group_by': None,
            'order_by': '-created_at',
            'sub_issue': True,
            'sub_group_by': None,
            'show_empty_groups': False,
            'calendar_date_range': '',
        }},
    }},
]

overview = IssueView.objects.get(id={overview_view_id!r})
overview.display_filters = view_specs[0]['display_filters']
overview.display_properties = base_display_properties
overview.filters = {{}}
overview.rich_filters = {{}}
overview.description = '默认甘特总览：展示浦江项目交付物、子任务和时间线。'
if overview.owned_by_id is None:
    overview.owned_by = owner
overview.save()

for spec in view_specs:
    view, _ = IssueView.objects.get_or_create(
        workspace=workspace,
        project=project,
        name=spec['name'],
        defaults={{
            'description': spec['description'],
            'filters': spec['filters'],
            'display_filters': spec['display_filters'],
            'display_properties': base_display_properties,
            'owned_by': owner,
            'access': 1,
        }},
    )
    view.description = spec['description']
    view.filters = spec['filters']
    view.rich_filters = rich_filter_converter.convert(spec['filters'], strict=False) if spec['filters'] else {{}}
    view.display_filters = spec['display_filters']
    view.display_properties = base_display_properties
    view.access = 1
    if view.owned_by_id is None:
        view.owned_by = owner
    if view.deleted_at is not None:
        view.deleted_at = None
    view.save()

print({{
    'labels': sorted(labels.keys()),
    'modules': sorted(modules.keys()),
    'views': [spec['name'] for spec in view_specs] + ['Overview'],
}})
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Plane visual constructs.")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE)
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument(
        "--owner-email",
        default=os.environ.get("PLANE_BOOTSTRAP_OWNER_EMAIL"),
        help="Optional Plane user email. If omitted, inferred from the existing view/project.",
    )
    parser.add_argument("--overview-view-id", default=DEFAULT_OVERVIEW_VIEW_ID)
    parser.add_argument("--sft-issue-id", default=DEFAULT_SFT_ISSUE_ID)
    parser.add_argument("--chunkmoe-issue-id", default=DEFAULT_CHUNKMOE_ISSUE_ID)
    args = parser.parse_args()

    script = DJANGO_SCRIPT.format(
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
    completed = subprocess.run(
        command,
        input=script,
        text=True,
        cwd=ROOT_DIR,
        check=False,
    )
    if completed.returncode != 0:
        return completed.returncode

    print(
        textwrap.dedent(
            f"""
            Plane visual constructs bootstrapped.
              workspace: {args.workspace}
              project_id: {args.project_id}
            """
        ).strip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
