#!/usr/bin/env python3
"""Export the latest portable Gantt snapshot and back it up to GitHub."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DELIVERY_DIR = ROOT_DIR / "exports/delivery"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "portable/gantt/latest"
PORTABLE_EXPORT_SCRIPT = ROOT_DIR / "scripts/export-gantt-portable.py"
DEFAULT_PROXY = "http://127.0.0.1:7890"


@dataclass(frozen=True)
class ChangesetCandidate:
    source: str
    path: Path
    payload: dict[str, Any]
    timestamp: float
    priority: int
    timestamp_label: str


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def run(
    args: list[str],
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )
    if check and result.returncode != 0:
        command = " ".join(args)
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{detail}")
    return result


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_timestamp(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def changeset_timestamp(path: Path, payload: dict[str, Any]) -> tuple[float, str]:
    for key in ("saved_at", "generated_at", "changeset_generated_at"):
        parsed = parse_timestamp(payload.get(key))
        if parsed is not None:
            return parsed, str(payload.get(key))
    try:
        return path.stat().st_mtime, f"mtime:{datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}"
    except OSError:
        return 0.0, "unknown"


def changeset_candidate(path: Path, source: str, priority: int) -> ChangesetCandidate | None:
    if not path.exists():
        return None
    payload = read_json(path)
    if not isinstance(payload, dict):
        return None
    snapshot = payload.get("snapshot")
    if not isinstance(snapshot, dict):
        return None
    if not isinstance(snapshot.get("tasks"), list) or not isinstance(snapshot.get("events"), list):
        return None
    timestamp, label = changeset_timestamp(path, payload)
    return ChangesetCandidate(source, path, payload, timestamp, priority, label)


def choose_latest_changeset(delivery_dir: Path, output_dir: Path) -> ChangesetCandidate | None:
    candidates = [
        changeset_candidate(delivery_dir / "gantt-autosave.json", "autosave", 30),
        changeset_candidate(delivery_dir / "gantt-local-edits.json", "pushed changes", 20),
        changeset_candidate(output_dir / "gantt-local-edits.json", "portable snapshot", 10),
    ]
    present = [candidate for candidate in candidates if candidate is not None]
    if not present:
        return None
    return sorted(present, key=lambda candidate: (candidate.timestamp, candidate.priority), reverse=True)[0]


def load_portable_exporter():
    spec = importlib.util.spec_from_file_location("export_gantt_portable", PORTABLE_EXPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {PORTABLE_EXPORT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.export_portable


def export_portable(delivery_dir: Path, output_dir: Path, candidate: ChangesetCandidate | None) -> dict[str, Any]:
    exporter = load_portable_exporter()
    changeset = candidate.payload if candidate else None
    return exporter(delivery_dir, output_dir, changeset=changeset)


def git_output(args: list[str], *, check: bool = True, env: dict[str, str] | None = None) -> str:
    return run(["git", *args], check=check, env=env).stdout.strip()


def has_portable_changes(output_dir: Path) -> bool:
    result = run(["git", "status", "--porcelain", "--", display_path(output_dir)], check=True)
    return bool(result.stdout.strip())


def staged_portable_changes(output_dir: Path) -> bool:
    result = run(["git", "diff", "--cached", "--quiet", "--", display_path(output_dir)], check=False)
    return result.returncode != 0


def remote_url(remote: str) -> str:
    result = run(["git", "remote", "get-url", remote], check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def push_env(remote: str, proxy: str | None) -> dict[str, str]:
    env = os.environ.copy()
    url = remote_url(remote)
    if proxy and "github.com" in url:
        proxy_url = proxy if "://" in proxy else f"http://{proxy}"
        env.setdefault("HTTPS_PROXY", proxy_url)
        env.setdefault("HTTP_PROXY", proxy_url)
    return env


def commit_and_push(output_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    if args.dry_run:
        return {"committed": False, "pushed": False, "dry_run": True}

    if args.branch:
        current = git_output(["branch", "--show-current"])
        if current != args.branch:
            raise RuntimeError(f"Current branch is {current!r}, expected {args.branch!r}; refusing to switch branches automatically.")

    if not args.commit:
        return {"committed": False, "pushed": False, "commit_disabled": True}

    if not has_portable_changes(output_dir):
        return {"committed": False, "pushed": False, "reason": "no portable changes"}

    git_output(["add", display_path(output_dir)])
    if not staged_portable_changes(output_dir):
        return {"committed": False, "pushed": False, "reason": "no staged portable changes"}

    stamp = datetime.now().strftime("%Y-%m-%d")
    message = args.message or f"data: backup portable gantt snapshot {stamp}"
    git_output(["commit", "-m", message])
    commit_hash = git_output(["rev-parse", "--short", "HEAD"])

    pushed = False
    if args.push:
        branch = args.branch or git_output(["branch", "--show-current"])
        git_output(["push", args.remote, branch], env=push_env(args.remote, args.proxy))
        pushed = True

    return {"committed": True, "commit": commit_hash, "pushed": pushed}


def print_summary(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up the latest portable Gantt snapshot to GitHub.")
    parser.add_argument("--delivery-dir", default=str(DEFAULT_DELIVERY_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default=None, help="Expected branch to push. The script fails if the current branch differs.")
    parser.add_argument("--message", default=None, help="Optional commit message.")
    parser.add_argument("--proxy", default=DEFAULT_PROXY, help="Proxy used for GitHub push. Use empty string to disable.")
    parser.add_argument("--no-commit", dest="commit", action="store_false", help="Export portable files without committing.")
    parser.add_argument("--no-push", dest="push", action="store_false", help="Commit without pushing.")
    parser.add_argument("--dry-run", action="store_true", help="Export portable files, then stop before git add/commit/push.")
    parser.set_defaults(commit=True, push=True)
    args = parser.parse_args()

    delivery_dir = Path(args.delivery_dir)
    if not delivery_dir.is_absolute():
        delivery_dir = ROOT_DIR / delivery_dir
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT_DIR / output_dir

    candidate = choose_latest_changeset(delivery_dir, output_dir)
    export_result = export_portable(delivery_dir, output_dir, candidate)
    git_result = commit_and_push(output_dir, args)

    summary = {
        "ok": True,
        "selected_changeset": {
            "source": candidate.source if candidate else "baseline",
            "path": display_path(candidate.path) if candidate else None,
            "timestamp": candidate.timestamp_label if candidate else None,
        },
        "portable": export_result,
        "git": git_result,
    }
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
