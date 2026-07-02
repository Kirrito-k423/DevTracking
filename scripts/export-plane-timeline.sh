#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/plane-selfhost/plane-app/plane.env"
COMPOSE_FILE="$ROOT_DIR/plane-selfhost/plane-app/docker-compose.yaml"
OUT_FILE="${1:-$ROOT_DIR/exports/plane/timeline.jsonl}"
SINCE="${SINCE:-1970-01-01T00:00:00Z}"

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
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v since="$SINCE" -At <<'SQL' > "$OUT_FILE"
copy (
  with issue_base as (
    select
      i.id as issue_id,
      i.workspace_id,
      i.project_id,
      p.name as project_name,
      p.identifier || '-' || i.sequence_id::text as issue_key,
      i.name as issue_title,
      i.priority,
      s.name as state_name,
      i.created_at,
      i.updated_at,
      i.completed_at
    from issues i
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
      ib.project_id,
      ib.project_name,
      ib.issue_id,
      ib.issue_key,
      ib.issue_title,
      null::text as actor,
      jsonb_build_object(
        'priority', ib.priority,
        'state', ib.state_name
      ) as payload
    from issue_base ib

    union all

    select
      ib.completed_at as event_time,
      'issue_completed' as event_type,
      ib.workspace_id,
      ib.project_id,
      ib.project_name,
      ib.issue_id,
      ib.issue_key,
      ib.issue_title,
      null::text as actor,
      jsonb_build_object(
        'priority', ib.priority,
        'state', ib.state_name
      ) as payload
    from issue_base ib
    where ib.completed_at is not null

    union all

    select
      ia.created_at as event_time,
      'issue_activity' as event_type,
      ia.workspace_id,
      ia.project_id,
      ib.project_name,
      ia.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(u.display_name, ''), nullif(u.email, ''), u.username) as actor,
      jsonb_build_object(
        'verb', ia.verb,
        'field', ia.field,
        'old_value', ia.old_value,
        'new_value', ia.new_value,
        'comment', ia.comment
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
      ic.project_id,
      ib.project_name,
      ic.issue_id,
      ib.issue_key,
      ib.issue_title,
      coalesce(nullif(u.display_name, ''), nullif(u.email, ''), u.username) as actor,
      jsonb_build_object(
        'comment', ic.comment_stripped,
        'access', ic.access
      ) as payload
    from issue_comments ic
    join issue_base ib on ib.issue_id = ic.issue_id
    left join users u on u.id = ic.actor_id
    where ic.deleted_at is null
  )
  select jsonb_build_object(
    'event_time', event_time,
    'event_type', event_type,
    'workspace_id', workspace_id,
    'project_id', project_id,
    'project', project_name,
    'issue_id', issue_id,
    'issue_key', issue_key,
    'issue_title', issue_title,
    'actor', actor,
    'payload', payload
  )
  from timeline
  where event_time >= :'since'::timestamptz
  order by event_time asc
) to stdout;
SQL

echo "Exported Plane timeline to $OUT_FILE"
