#!/usr/bin/env python3
"""Export the read-only Plane timeline on Windows, macOS, or Linux."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / "plane-selfhost/plane-app/plane.env"
COMPOSE_FILE = ROOT_DIR / "plane-selfhost/plane-app/docker-compose.yaml"
QUERY_SOURCE = ROOT_DIR / "scripts/export-plane-timeline.sh"
DEFAULT_OUTPUT = ROOT_DIR / "exports/plane/timeline.jsonl"


def timeline_query() -> str:
    """Reuse the canonical SQL embedded in the POSIX launcher."""
    source = QUERY_SOURCE.read_text(encoding="utf-8")
    marker = "<<'SQL'"
    marker_at = source.find(marker)
    if marker_at < 0:
        raise RuntimeError(f"SQL start marker not found in {QUERY_SOURCE}")
    query_start = source.find("\n", marker_at)
    query_end = source.rfind("\nSQL")
    if query_start < 0 or query_end <= query_start:
        raise RuntimeError(f"SQL end marker not found in {QUERY_SOURCE}")
    return source[query_start + 1 : query_end] + "\n"


def export_timeline(since: str, output: Path) -> None:
    if not ENV_FILE.is_file():
        raise FileNotFoundError(f"Plane env file not found: {ENV_FILE}")
    if not COMPOSE_FILE.is_file():
        raise FileNotFoundError(f"Plane compose file not found: {COMPOSE_FILE}")
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("Docker CLI was not found. Install/start Docker Desktop and ensure docker.exe is on PATH.")

    command = [
        docker,
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "--env-file",
        str(ENV_FILE),
        "exec",
        "-T",
        "plane-db",
        "sh",
        "-lc",
        'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -X -q -v ON_ERROR_STOP=1 -v "since=$1" -At',
        "plane-timeline-export",
        since,
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT_DIR,
        input=timeline_query().encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Plane timeline export failed ({completed.returncode}): {detail}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a read-only Plane timeline as JSONL.")
    parser.add_argument("output_positional", nargs="?", help="Optional output JSONL path.")
    parser.add_argument("--since", default="1970-01-01T00:00:00Z")
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    output = Path(args.output or args.output_positional or DEFAULT_OUTPUT)
    if not output.is_absolute():
        output = ROOT_DIR / output
    try:
        export_timeline(args.since, output)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Exported Plane timeline to {output} since {args.since}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
