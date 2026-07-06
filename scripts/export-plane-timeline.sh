#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/plane-selfhost/plane-app/plane.env"
COMPOSE_FILE="$ROOT_DIR/plane-selfhost/plane-app/docker-compose.yaml"
SINCE="${SINCE:-1970-01-01T00:00:00Z}"
OUT_FILE="$ROOT_DIR/exports/plane/timeline.jsonl"

usage() {
  cat <<'USAGE'
Usage:
  scripts/export-plane-timeline.sh [output.jsonl]
  scripts/export-plane-timeline.sh --since 2026-07-01T00:00:00Z --output exports/plane/timeline.jsonl

Environment:
  SINCE  Default lower bound for event_time when --since is not provided.

Exports a read-only Plane timeline as JSONL. Normal Plane writes must use API-level behavior, not this script.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --since)
      SINCE="${2:?missing value for --since}"
      shift 2
      ;;
    --output|-o)
      OUT_FILE="${2:?missing value for --output}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      OUT_FILE="$1"
      shift
      ;;
  esac
done

case "$OUT_FILE" in
  /*) ;;
  *) OUT_FILE="$ROOT_DIR/$OUT_FILE" ;;
esac

if [ ! -f "$ENV_FILE" ]; then
  echo "Plane env file not found: $ENV_FILE" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT_FILE")"

set -a
. "$ENV_FILE"
set +a

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
  exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" plane-db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -X -q -v ON_ERROR_STOP=1 -v since="$SINCE" -At <<'SQL' > "$OUT_FILE"
begin read only;
copy (
  with issue_base as (
    select
      i.id as issue_id,
      i.workspace_id,
      w.slug as workspace_slug,
      w.name as workspace_name,
      i.project_id,
      p.name as project_name,
      p.identifier || '-' || i.sequence_id::text as issue_key,
      i.name as issue_title,
      i.parent_id,
      i.start_date,
      i.target_date,
      i.priority,
      s.name as state_name,
      i.created_at,
      i.updated_at,
      i.completed_at,
      jsonb_build_object(
        'parent_id', i.parent_id,
        'start_date', i.start_date,
        'target_date', i.target_date,
        'completed_at', i.completed_at,
        'priority', i.priority,
        'state', s.name
      ) as current_issue
    from issues i
    join workspaces w on w.id = i.workspace_id
    join projects p on p.id = i.project_id
    left join states s on s.id = i.state_id
    where i.deleted_at is null
      and p.deleted_at is null
  ),
  timeline as (
    select
      ib.created_at as event_time,
      'issue_created' as event_type,
      ib.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      ib.project_id,
      ib.project_name,
      ib.issue_id,
      ib.issue_key,
      ib.issue_title,
      null::text as actor,
      jsonb_build_object(
        'table', 'issues',
        'id', ib.issue_id,
        'field', 'created_at'
      ) as source,
      ib.current_issue as payload
    from issue_base ib

    union all

    select
      ib.completed_at as event_time,
      'issue_completed' as event_type,
      ib.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      ib.project_id,
      ib.project_name,
      ib.issue_id,
      ib.issue_key,
      ib.issue_title,
      null::text as actor,
      jsonb_build_object(
        'table', 'issues',
        'id', ib.issue_id,
        'field', 'completed_at'
      ) as source,
      ib.current_issue as payload
    from issue_base ib
    where ib.completed_at is not null

    union all

    select
      ia.created_at as event_time,
      'issue_activity' as event_type,
      ia.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      ia.project_id,
      ib.project_name,
      ia.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(u.display_name, ''), nullif(u.email, ''), u.username) as actor,
      jsonb_build_object(
        'table', 'issue_activities',
        'id', ia.id,
        'field', ia.field
      ) as source,
      jsonb_build_object(
        'verb', ia.verb,
        'field', ia.field,
        'old_value', ia.old_value,
        'new_value', ia.new_value,
        'comment', ia.comment,
        'current_issue', ib.current_issue
      ) as payload
    from issue_activities ia
    join issue_base ib on ib.issue_id = ia.issue_id
    left join users u on u.id = ia.actor_id
    where ia.deleted_at is null

    union all

    select
      ic.created_at as event_time,
      'issue_comment' as event_type,
      ic.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      ic.project_id,
      ib.project_name,
      ic.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(u.display_name, ''), nullif(u.email, ''), u.username) as actor,
      jsonb_build_object(
        'table', 'issue_comments',
        'id', ic.id
      ) as source,
      jsonb_build_object(
        'comment', ic.comment_stripped,
        'access', ic.access,
        'current_issue', ib.current_issue
      ) as payload
    from issue_comments ic
    join issue_base ib on ib.issue_id = ic.issue_id
    left join users u on u.id = ic.actor_id
    where ic.deleted_at is null

    union all

    select
      ias.created_at as event_time,
      'assignee_added' as event_type,
      ias.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      ias.project_id,
      ib.project_name,
      ias.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(cu.display_name, ''), nullif(cu.email, ''), cu.username) as actor,
      jsonb_build_object(
        'table', 'issue_assignees',
        'id', ias.id
      ) as source,
      jsonb_build_object(
        'assignee_id', au.id,
        'assignee', coalesce(nullif(au.display_name, ''), nullif(au.email, ''), au.username),
        'current_issue', ib.current_issue
      ) as payload
    from issue_assignees ias
    join issue_base ib on ib.issue_id = ias.issue_id
    left join users cu on cu.id = ias.created_by_id
    left join users au on au.id = ias.assignee_id
    where ias.deleted_at is null

    union all

    select
      ci.created_at as event_time,
      'cycle_linked' as event_type,
      ci.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      ci.project_id,
      ib.project_name,
      ci.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(cu.display_name, ''), nullif(cu.email, ''), cu.username) as actor,
      jsonb_build_object(
        'table', 'cycle_issues',
        'id', ci.id
      ) as source,
      jsonb_build_object(
        'cycle_id', c.id,
        'cycle', c.name,
        'start_date', c.start_date,
        'end_date', c.end_date,
        'current_issue', ib.current_issue
      ) as payload
    from cycle_issues ci
    join issue_base ib on ib.issue_id = ci.issue_id
    left join cycles c on c.id = ci.cycle_id
    left join users cu on cu.id = ci.created_by_id
    where ci.deleted_at is null
      and (c.deleted_at is null or c.id is null)

    union all

    select
      mi.created_at as event_time,
      'module_linked' as event_type,
      mi.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      mi.project_id,
      ib.project_name,
      mi.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(cu.display_name, ''), nullif(cu.email, ''), cu.username) as actor,
      jsonb_build_object(
        'table', 'module_issues',
        'id', mi.id
      ) as source,
      jsonb_build_object(
        'module_id', m.id,
        'module', m.name,
        'status', m.status,
        'start_date', m.start_date,
        'target_date', m.target_date,
        'current_issue', ib.current_issue
      ) as payload
    from module_issues mi
    join issue_base ib on ib.issue_id = mi.issue_id
    left join modules m on m.id = mi.module_id
    left join users cu on cu.id = mi.created_by_id
    where mi.deleted_at is null
      and (m.deleted_at is null or m.id is null)

    union all

    select
      il.created_at as event_time,
      'label_added' as event_type,
      il.workspace_id,
      ib.workspace_slug,
      ib.workspace_name,
      il.project_id,
      ib.project_name,
      il.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(cu.display_name, ''), nullif(cu.email, ''), cu.username) as actor,
      jsonb_build_object(
        'table', 'issue_labels',
        'id', il.id
      ) as source,
      jsonb_build_object(
        'label_id', l.id,
        'label', l.name,
        'color', l.color,
        'current_issue', ib.current_issue
      ) as payload
    from issue_labels il
    join issue_base ib on ib.issue_id = il.issue_id
    left join labels l on l.id = il.label_id
    left join users cu on cu.id = il.created_by_id
    where il.deleted_at is null
      and (l.deleted_at is null or l.id is null)
  )
  select jsonb_build_object(
    'event_time', event_time,
    'event_type', event_type,
    'workspace_id', workspace_id,
    'workspace_slug', workspace_slug,
    'workspace', workspace_name,
    'project_id', project_id,
    'project', project_name,
    'issue_id', issue_id,
    'issue_key', issue_key,
    'issue_title', issue_title,
    'actor', actor,
    'source', source,
    'payload', payload
  )
  from timeline
  where event_time >= :'since'::timestamptz
  order by event_time asc
) to stdout;
commit;
SQL

echo "Exported Plane timeline to $OUT_FILE since $SINCE"
