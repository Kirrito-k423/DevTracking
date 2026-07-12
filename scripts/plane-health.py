#!/usr/bin/env python3
"""Check the local Plane deployment without requiring a POSIX shell."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / "plane-selfhost/plane-app/plane.env"
COMPOSE_FILE = ROOT_DIR / "plane-selfhost/plane-app/docker-compose.yaml"
EXPECTED_SERVICES = ("proxy", "web", "api", "worker", "plane-db", "plane-redis", "plane-mq")


def env_value(name: str, default: str = "") -> str:
    if not ENV_FILE.is_file():
        return default
    prefix = name + "="
    for raw_line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if line.startswith(prefix):
            return line[len(prefix) :].strip().strip('"').strip("'")
    return default


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT_DIR, text=True, capture_output=True, check=False, encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the local Plane HTTP, Docker services, and read-only database access.")
    parser.add_argument("--url", default="http://localhost:8090")
    args = parser.parse_args()

    if not ENV_FILE.is_file():
        print(f"FAIL env_file missing: {ENV_FILE}", file=sys.stderr)
        return 1
    if not COMPOSE_FILE.is_file():
        print(f"FAIL compose_file missing: {COMPOSE_FILE}", file=sys.stderr)
        return 1
    docker = shutil.which("docker")
    if not docker:
        print("FAIL Docker CLI not found. Install/start Docker Desktop and ensure docker.exe is on PATH.", file=sys.stderr)
        return 1

    print("Plane health")
    print(f"  url: {args.url}")
    print(f"  configured_release: {env_value('APP_RELEASE', 'v1.3.1')}")
    print("  compose_file: plane-selfhost/plane-app/docker-compose.yaml")
    print("  env_file: plane-selfhost/plane-app/plane.env (loaded by Docker; values redacted)")
    try:
        with urllib.request.urlopen(args.url, timeout=8) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  http: FAIL {exc}", file=sys.stderr)
        return 1
    if status < 200 or status >= 400:
        print(f"  http: FAIL status={status}", file=sys.stderr)
        return 1
    print(f"  http: PASS status={status}")

    base = [docker, "compose", "-f", str(COMPOSE_FILE), "--env-file", str(ENV_FILE)]
    print("\nDocker services")
    services = run([*base, "ps", "--services", "--filter", "status=running"])
    if services.returncode != 0:
        print(services.stderr.strip() or "  FAIL unable to query Docker Compose", file=sys.stderr)
        return services.returncode or 1
    running = set(services.stdout.split())
    missing = [service for service in EXPECTED_SERVICES if service not in running]
    for service in EXPECTED_SERVICES:
        state = "PASS running" if service in running else "FAIL not running"
        print(f"  service:{service} {state}")
    if missing:
        return 1

    db_command = [
        *base,
        "exec",
        "-T",
        "plane-db",
        "sh",
        "-lc",
        'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -X -q -t -A -c "select count(*) from information_schema.tables where table_schema = \'public\';"',
    ]
    db_check = run(db_command)
    table_count = db_check.stdout.strip()
    if db_check.returncode != 0 or not table_count.isdigit() or int(table_count) <= 0:
        print("\nDatabase\n  read_check: FAIL", file=sys.stderr)
        if db_check.stderr.strip():
            print(db_check.stderr.strip(), file=sys.stderr)
        return db_check.returncode or 1
    print(f"\nDatabase\n  read_check: PASS public_tables={table_count}")
    print("\nPlane health check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
