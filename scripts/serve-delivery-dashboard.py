#!/usr/bin/env python3
"""Serve delivery exports and persist Gantt edit changesets locally."""

from __future__ import annotations

import argparse
import io
import importlib.util
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT_DIR / "exports/delivery"
PORTABLE_DIRECTORY = ROOT_DIR / "portable/gantt/latest"
PORTABLE_EXPORT_SCRIPT = ROOT_DIR / "scripts/export-gantt-portable.py"
AUTOSAVE_HISTORY_LIMIT = 200
PORTABLE_ZIP_LIMIT = 20_000_000
PORTABLE_IMPORT_FILES = {
    "gantt.html",
    "gantt.json",
    "gantt-local-edits.json",
    "manifest.json",
    "README.md",
    "start-windows.bat",
    "start-windows.ps1",
    "start-macos-linux.sh",
}


class DeliveryHandler(SimpleHTTPRequestHandler):
    portable_directory = PORTABLE_DIRECTORY

    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(DEFAULT_DIRECTORY), **kwargs)

    def do_GET(self) -> None:
        route = self.path.rstrip("/")
        if route == "/api/gantt-autosave/latest":
            self._send_latest_gantt_autosave()
            return
        if route == "/api/gantt-edits/latest":
            self._send_latest_gantt_edits()
            return
        if route == "/api/gantt-portable/latest":
            self._send_latest_portable_gantt()
            return
        if route == "/api/gantt-portable/manifest":
            self._send_portable_manifest()
            return
        if route == "/api/gantt-portable/download":
            self._download_portable_zip()
            return
        super().do_GET()

    def do_POST(self) -> None:
        route = self.path.rstrip("/")
        if route == "/api/gantt-portable/import":
            self._import_portable_zip()
            return
        if route not in {"/api/gantt-autosave", "/api/gantt-edits", "/api/gantt-portable/export"}:
            self.send_error(404, "Unknown API route")
            return

        payload = self._read_json_payload()
        if payload is None:
            return

        changeset = payload.get("changeset")
        if not isinstance(changeset, dict):
            self.send_error(400, "Missing changeset object")
            return

        if route == "/api/gantt-portable/export":
            self._export_portable_gantt(changeset)
            return
        if route == "/api/gantt-autosave":
            self._persist_gantt_autosave(payload, changeset)
            return

        self._persist_gantt_edits(payload, changeset)

    def _read_json_payload(self) -> dict | None:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0 or content_length > 5_000_000:
            self.send_error(413, "Invalid changeset size")
            return None

        try:
            return json.loads(self.rfile.read(content_length).decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return None

    def _persist_gantt_edits(self, payload: dict, changeset: dict) -> None:
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

    def _persist_gantt_autosave(self, payload: dict, changeset: dict) -> None:
        root = Path(self.directory).resolve()
        autosave_dir = root / "gantt-autosaves"
        autosave_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        filename = self._safe_filename(str(payload.get("filename") or f"gantt-autosave-{stamp}.json"))
        timestamped_path = autosave_dir / filename
        latest_path = root / "gantt-autosave.json"

        encoded = json.dumps(changeset, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        timestamped_path.write_text(encoded, encoding="utf-8")
        latest_path.write_text(encoded, encoding="utf-8")
        self._prune_autosaves(autosave_dir)

        response = {
            "ok": True,
            "path": str(timestamped_path.relative_to(ROOT_DIR)),
            "latest": str(latest_path.relative_to(ROOT_DIR)),
            "history_limit": AUTOSAVE_HISTORY_LIMIT,
        }
        self._send_json(200, response)

    def _prune_autosaves(self, autosave_dir: Path) -> None:
        files = sorted(autosave_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        for old_file in files[AUTOSAVE_HISTORY_LIMIT:]:
            old_file.unlink(missing_ok=True)

    def _send_latest_gantt_autosave(self) -> None:
        latest_path = Path(self.directory).resolve() / "gantt-autosave.json"
        if not latest_path.exists():
            self._send_json(404, {"ok": False, "reason": "no_autosave"})
            return
        try:
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._send_json(500, {"ok": False, "reason": "invalid_autosave"})
            return
        self._send_json(200, {"ok": True, "changeset": payload})

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

    def _send_latest_portable_gantt(self) -> None:
        latest_path = self.portable_directory / "gantt-local-edits.json"
        if not latest_path.exists():
            self._send_json(404, {"ok": False, "reason": "no_portable_snapshot"})
            return
        try:
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._send_json(500, {"ok": False, "reason": "invalid_portable_snapshot"})
            return
        self._send_json(200, {"ok": True, "changeset": payload})

    def _send_portable_manifest(self) -> None:
        manifest_path = self.portable_directory / "manifest.json"
        if not manifest_path.exists():
            self._send_json(404, {"ok": False, "reason": "no_portable_manifest"})
            return
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._send_json(500, {"ok": False, "reason": "invalid_portable_manifest"})
            return
        self._send_json(200, {"ok": True, "manifest": payload})

    def _export_portable_gantt(self, changeset: dict) -> None:
        try:
            exporter = _load_portable_exporter()
            result = exporter(Path(self.directory), self.portable_directory, changeset=changeset)
        except Exception as exc:  # noqa: BLE001 - local tool should surface exact export failure.
            self._send_json(500, {"ok": False, "reason": "portable_export_failed", "error": str(exc)})
            return
        self._send_json(200, result)

    def _download_portable_zip(self) -> None:
        portable_dir = self.portable_directory
        if not (portable_dir / "gantt-local-edits.json").exists():
            self._send_json(404, {"ok": False, "reason": "no_portable_snapshot"})
            return

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(portable_dir.iterdir()):
                if path.is_file() and path.name in PORTABLE_IMPORT_FILES:
                    archive.write(path, arcname=path.name)
        body = buffer.getvalue()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="plane-demand-hub-gantt-{stamp}.zip"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _import_portable_zip(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0 or content_length > PORTABLE_ZIP_LIMIT:
            self.send_error(413, "Invalid portable package size")
            return
        raw = self.rfile.read(content_length)

        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                files = self._read_portable_zip_files(archive)
        except (zipfile.BadZipFile, ValueError) as exc:
            self._send_json(400, {"ok": False, "reason": "invalid_portable_zip", "error": str(exc)})
            return

        changeset = files.get("gantt-local-edits.json")
        if not isinstance(changeset, dict) or not self._valid_changeset_snapshot(changeset):
            self._send_json(400, {"ok": False, "reason": "missing_valid_changeset"})
            return

        portable_dir = self.portable_directory
        portable_dir.mkdir(parents=True, exist_ok=True)
        for name, payload in files.items():
            target = portable_dir / name
            if isinstance(payload, dict):
                target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            else:
                target.write_text(payload, encoding="utf-8")
            if name == "start-macos-linux.sh":
                target.chmod(target.stat().st_mode | 0o755)

        root = Path(self.directory).resolve()
        root.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(changeset, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        (root / "gantt-local-edits.json").write_text(encoded, encoding="utf-8")
        (root / "gantt-autosave.json").write_text(encoded, encoding="utf-8")
        counts = {
            "tasks": len(changeset.get("snapshot", {}).get("tasks") or []),
            "events": len(changeset.get("snapshot", {}).get("events") or []),
        }
        self._send_json(200, {"ok": True, "changeset": changeset, "counts": counts})

    def _read_portable_zip_files(self, archive: zipfile.ZipFile) -> dict[str, dict | str]:
        files: dict[str, dict | str] = {}
        for info in archive.infolist():
            name = Path(info.filename).name
            if not name or name != info.filename or name not in PORTABLE_IMPORT_FILES:
                continue
            if info.file_size > PORTABLE_ZIP_LIMIT:
                raise ValueError(f"{name} is too large")
            data = archive.read(info)
            if name.endswith(".json"):
                files[name] = json.loads(data.decode("utf-8"))
            else:
                files[name] = data.decode("utf-8")
        return files

    @staticmethod
    def _valid_changeset_snapshot(changeset: dict) -> bool:
        snapshot = changeset.get("snapshot")
        return (
            isinstance(snapshot, dict)
            and isinstance(snapshot.get("tasks"), list)
            and isinstance(snapshot.get("events"), list)
        )

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


def _load_portable_exporter():
    spec = importlib.util.spec_from_file_location("export_gantt_portable", PORTABLE_EXPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {PORTABLE_EXPORT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.export_portable


def prepare_directory_from_portable(directory: Path, portable_directory: Path = PORTABLE_DIRECTORY) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "gantt.html").exists():
        return
    if not (portable_directory / "gantt.html").exists():
        return
    for name in ["gantt.html", "gantt.json", "gantt-local-edits.json"]:
        source = portable_directory / name
        if source.exists() and source.resolve() != (directory / name).resolve():
            shutil.copy2(source, directory / name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve delivery exports with a local Gantt changeset API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--directory", default=str(DEFAULT_DIRECTORY))
    parser.add_argument("--portable-directory", default=str(PORTABLE_DIRECTORY))
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_absolute():
        directory = ROOT_DIR / directory
    portable_directory = Path(args.portable_directory)
    if not portable_directory.is_absolute():
        portable_directory = ROOT_DIR / portable_directory
    DeliveryHandler.portable_directory = portable_directory
    prepare_directory_from_portable(directory, portable_directory)

    def handler(*handler_args, **handler_kwargs):
        return DeliveryHandler(*handler_args, directory=str(directory), **handler_kwargs)

    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {directory} at http://{args.host}:{args.port}")
    print("Gantt changesets POST to /api/gantt-edits")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
