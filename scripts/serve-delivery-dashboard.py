#!/usr/bin/env python3
"""Serve delivery exports and persist Gantt edit changesets locally."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT_DIR / "exports/delivery"


class DeliveryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(DEFAULT_DIRECTORY), **kwargs)

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/api/gantt-edits/latest":
            self._send_latest_gantt_edits()
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/api/gantt-edits":
            self.send_error(404, "Unknown API route")
            return

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0 or content_length > 5_000_000:
            self.send_error(413, "Invalid changeset size")
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        changeset = payload.get("changeset")
        if not isinstance(changeset, dict):
            self.send_error(400, "Missing changeset object")
            return

        filename = self._safe_filename(str(payload.get("filename") or ""))
        if not filename:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            filename = f"gantt-changeset-{stamp}.json"

        root = Path(self.directory).resolve()
        changeset_dir = root / "gantt-changesets"
        changeset_dir.mkdir(parents=True, exist_ok=True)
        timestamped_path = changeset_dir / filename
        latest_path = root / "gantt-local-edits.json"

        encoded = json.dumps(changeset, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        timestamped_path.write_text(encoded, encoding="utf-8")
        latest_path.write_text(encoded, encoding="utf-8")

        response = {
            "ok": True,
            "path": str(timestamped_path.relative_to(ROOT_DIR)),
            "latest": str(latest_path.relative_to(ROOT_DIR)),
            "write_boundary": "Local changeset only. Applying to Plane requires a controlled API writer.",
        }
        self._send_json(200, response)

    def _send_latest_gantt_edits(self) -> None:
        latest_path = Path(self.directory).resolve() / "gantt-local-edits.json"
        if not latest_path.exists():
            self._send_json(404, {"ok": False, "reason": "no_saved_changeset"})
            return
        try:
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._send_json(500, {"ok": False, "reason": "invalid_saved_changeset"})
            return
        self._send_json(200, {"ok": True, "changeset": payload})

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _safe_filename(value: str) -> str:
        name = Path(value).name
        if not name.endswith(".json"):
            name += ".json"
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
        return name[:160]


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve delivery exports with a local Gantt changeset API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--directory", default=str(DEFAULT_DIRECTORY))
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_absolute():
        directory = ROOT_DIR / directory
    directory.mkdir(parents=True, exist_ok=True)

    def handler(*handler_args, **handler_kwargs):
        return DeliveryHandler(*handler_args, directory=str(directory), **handler_kwargs)

    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {directory} at http://{args.host}:{args.port}")
    print("Gantt changesets POST to /api/gantt-edits")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
