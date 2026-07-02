#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/plane-selfhost/plane-app/plane.env"
COMPOSE_FILE="$ROOT_DIR/plane-selfhost/plane-app/docker-compose.yaml"
PLANE_URL="${PLANE_URL:-http://localhost:8090}"

usage() {
  cat <<'USAGE'
Usage:
  scripts/plane-health.sh [--url http://localhost:8090]

Checks the local Plane deployment without printing secrets.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --url)
      PLANE_URL="${2:?missing value for --url}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ ! -f "$ENV_FILE" ]; then
  echo "FAIL env_file missing: $ENV_FILE" >&2
  exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "FAIL compose_file missing: $COMPOSE_FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

APP_RELEASE_SAFE="${APP_RELEASE:-v1.3.1}"

echo "Plane health"
echo "  url: $PLANE_URL"
echo "  configured_release: $APP_RELEASE_SAFE"
echo "  compose_file: plane-selfhost/plane-app/docker-compose.yaml"
echo "  env_file: plane-selfhost/plane-app/plane.env (loaded, values redacted)"

HTTP_STATUS="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 "$PLANE_URL" || true)"
if [[ "$HTTP_STATUS" =~ ^(2|3)[0-9][0-9]$ ]]; then
  echo "  http: PASS status=$HTTP_STATUS"
else
  echo "  http: FAIL status=${HTTP_STATUS:-none}" >&2
  exit 1
fi

echo
echo "Docker services"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

RUNNING_SERVICES="$(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --services --filter status=running 2>/dev/null || true)"
for service in proxy web api worker plane-db plane-redis plane-mq; do
  if printf '%s\n' "$RUNNING_SERVICES" | grep -qx "$service"; then
    echo "  service:$service PASS running"
  else
    echo "  service:$service FAIL not running" >&2
    exit 1
  fi
done

DB_CHECK="$(
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" \
    exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" plane-db \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -X -q -t -A \
      -c "select count(*) from information_schema.tables where table_schema = 'public';"
)"

if [[ "$DB_CHECK" =~ ^[0-9]+$ ]] && [ "$DB_CHECK" -gt 0 ]; then
  echo
  echo "Database"
  echo "  read_check: PASS public_tables=$DB_CHECK"
else
  echo "  read_check: FAIL" >&2
  exit 1
fi

echo
echo "Plane health check passed"

