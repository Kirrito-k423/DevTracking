#!/usr/bin/env python3
"""Serve delivery exports and persist Gantt edit changesets locally."""

from __future__ import annotations

import argparse
import hashlib
import io
import importlib.util
import json
import mimetypes
import re
import shutil
import zipfile
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, quote, unquote, urlsplit


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT_DIR / "exports/delivery"
PORTABLE_DIRECTORY = ROOT_DIR / "portable/gantt/latest"
PORTABLE_EXPORT_SCRIPT = ROOT_DIR / "scripts/export-gantt-portable.py"
AUTOSAVE_HISTORY_LIMIT = 200
ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024
PORTABLE_ZIP_LIMIT = 512 * 1024 * 1024
PORTABLE_UNCOMPRESSED_LIMIT = 1024 * 1024 * 1024
ATTACHMENT_DIRECTORY = "gantt-attachments"
ATTACHMENT_EXTENSIONS = {
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".txt",
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
}
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


def display_path(path: Path) -> str:
    """Return a readable path without assuming runtime data lives in the repo."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT_DIR))
    except ValueError:
        return str(resolved)


class DeliveryHandler(SimpleHTTPRequestHandler):
    portable_directory = PORTABLE_DIRECTORY

    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(DEFAULT_DIRECTORY), **kwargs)

    def do_GET(self) -> None:
        route = self._route_path()
        if route.startswith("/api/gantt-attachments/"):
            self._send_attachment(route)
            return
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
        route = self._route_path()
        if route == "/api/gantt-attachments":
            self._upload_attachment()
            return
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

    def do_DELETE(self) -> None:
        route = self._route_path()
        if route.startswith("/api/gantt-attachments/"):
            self._delete_attachment(route)
            return
        self.send_error(404, "Unknown API route")

    def _upload_attachment(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0 or content_length > ATTACHMENT_MAX_BYTES:
            self._send_json(413, {"ok": False, "reason": "attachment_size_limit", "max_bytes": ATTACHMENT_MAX_BYTES})
            return

        query = parse_qs(urlsplit(self.path).query)
        attachment_id = self._safe_attachment_id((query.get("id") or [""])[0])
        original_name = Path(unquote((query.get("name") or [""])[0])).name
        suffix = Path(original_name).suffix.lower()
        original_name = f"{Path(original_name).stem[:220]}{suffix}"
        if not attachment_id or not original_name or suffix not in ATTACHMENT_EXTENSIONS:
            self._send_json(415, {"ok": False, "reason": "unsupported_attachment_type"})
            return

        body = self.rfile.read(content_length)
        storage_name = f"{attachment_id}{suffix}"
        attachment_dir = Path(self.directory).resolve() / ATTACHMENT_DIRECTORY
        attachment_dir.mkdir(parents=True, exist_ok=True)
        for old_path in attachment_dir.glob(f"{attachment_id}.*"):
            if old_path.is_file():
                old_path.unlink(missing_ok=True)
        target = attachment_dir / storage_name
        temporary = attachment_dir / f".{storage_name}.uploading"
        temporary.write_bytes(body)
        temporary.replace(target)
        content_type = (query.get("content_type") or [""])[0].strip()[:160]
        if not content_type:
            content_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        self._send_json(201, {
            "ok": True,
            "attachment": {
                "id": attachment_id,
                "name": original_name,
                "storage_name": storage_name,
                "content_type": content_type,
                "size": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "url": self._attachment_url(storage_name),
            },
        })

    def _send_attachment(self, route: str) -> None:
        storage_name = self._safe_attachment_storage_name(unquote(route.rsplit("/", 1)[-1]))
        if not storage_name:
            self.send_error(404, "Attachment not found")
            return
        candidates = [
            Path(self.directory).resolve() / ATTACHMENT_DIRECTORY / storage_name,
            self.portable_directory.resolve() / ATTACHMENT_DIRECTORY / storage_name,
        ]
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            self.send_error(404, "Attachment not found")
            return
        body = source.read_bytes()
        content_type = mimetypes.guess_type(storage_name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Disposition", f"inline; filename*=UTF-8''{quote(storage_name)}")
        self.end_headers()
        self.wfile.write(body)

    def _delete_attachment(self, route: str) -> None:
        storage_name = self._safe_attachment_storage_name(unquote(route.rsplit("/", 1)[-1]))
        if not storage_name:
            self._send_json(400, {"ok": False, "reason": "invalid_attachment_name"})
            return
        target = Path(self.directory).resolve() / ATTACHMENT_DIRECTORY / storage_name
        deleted = target.is_file()
        target.unlink(missing_ok=True)
        self._send_json(200, {"ok": True, "deleted": deleted})

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
            "path": display_path(timestamped_path),
            "latest": display_path(latest_path),
            "write_boundary": "Local changeset only; the standalone Gantt never writes to an external task system.",
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
            "path": display_path(timestamped_path),
            "latest": display_path(latest_path),
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
            for path in sorted(portable_dir.rglob("*")):
                if not path.is_file() or path.is_symlink():
                    continue
                relative = path.relative_to(portable_dir).as_posix()
                if self._portable_archive_path_allowed(relative):
                    archive.write(path, arcname=relative)
        body = buffer.getvalue()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="delivery-gantt-{stamp}.zip"')
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

        try:
            expected_attachments = self._changeset_attachment_names(changeset)
        except ValueError as exc:
            self._send_json(400, {"ok": False, "reason": "invalid_attachment_metadata", "error": str(exc)})
            return
        imported_attachments = {name for name in files if name.startswith(f"{ATTACHMENT_DIRECTORY}/")}
        missing_attachments = expected_attachments - imported_attachments
        if missing_attachments:
            self._send_json(400, {
                "ok": False,
                "reason": "missing_attachment_files",
                "files": sorted(missing_attachments),
            })
            return
        unexpected_attachments = imported_attachments - expected_attachments
        if unexpected_attachments:
            self._send_json(400, {
                "ok": False,
                "reason": "unexpected_attachment_files",
                "files": sorted(unexpected_attachments),
            })
            return

        portable_dir = self.portable_directory
        portable_dir.mkdir(parents=True, exist_ok=True)
        self._replace_attachment_directory(portable_dir, files)
        for name, payload in files.items():
            if name.startswith(f"{ATTACHMENT_DIRECTORY}/"):
                continue
            target = portable_dir / name
            if isinstance(payload, dict):
                target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            else:
                target.write_text(payload, encoding="utf-8")
            if name == "start-macos-linux.sh":
                target.chmod(target.stat().st_mode | 0o755)

        root = Path(self.directory).resolve()
        root.mkdir(parents=True, exist_ok=True)
        self._replace_attachment_directory(root, files)
        encoded = json.dumps(changeset, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        (root / "gantt-local-edits.json").write_text(encoded, encoding="utf-8")
        (root / "gantt-autosave.json").write_text(encoded, encoding="utf-8")
        counts = {
            "tasks": len(changeset.get("snapshot", {}).get("tasks") or []),
            "events": len(changeset.get("snapshot", {}).get("events") or []),
            "attachments": len(changeset.get("snapshot", {}).get("attachments") or []),
        }
        self._send_json(200, {"ok": True, "changeset": changeset, "counts": counts})

    def _read_portable_zip_files(self, archive: zipfile.ZipFile) -> dict[str, dict | str | bytes]:
        files: dict[str, dict | str | bytes] = {}
        total_size = 0
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = PurePosixPath(info.filename).as_posix()
            if not self._portable_archive_path_allowed(name):
                if ".." in PurePosixPath(info.filename).parts or PurePosixPath(info.filename).is_absolute():
                    raise ValueError(f"unsafe archive path: {info.filename}")
                continue
            is_attachment = name.startswith(f"{ATTACHMENT_DIRECTORY}/")
            file_limit = ATTACHMENT_MAX_BYTES if is_attachment else PORTABLE_ZIP_LIMIT
            if info.file_size > file_limit:
                raise ValueError(f"{name} is too large")
            total_size += info.file_size
            if total_size > PORTABLE_UNCOMPRESSED_LIMIT:
                raise ValueError("portable package is too large after decompression")
            data = archive.read(info)
            if is_attachment:
                files[name] = data
            elif name.endswith(".json"):
                files[name] = json.loads(data.decode("utf-8"))
            else:
                files[name] = data.decode("utf-8")
        return files

    def _replace_attachment_directory(self, root: Path, files: dict[str, dict | str | bytes]) -> None:
        attachment_dir = root / ATTACHMENT_DIRECTORY
        if attachment_dir.exists():
            shutil.rmtree(attachment_dir)
        payloads = {
            name.split("/", 1)[1]: payload
            for name, payload in files.items()
            if name.startswith(f"{ATTACHMENT_DIRECTORY}/") and isinstance(payload, bytes)
        }
        if not payloads:
            return
        attachment_dir.mkdir(parents=True, exist_ok=True)
        for storage_name, payload in payloads.items():
            (attachment_dir / storage_name).write_bytes(payload)

    @classmethod
    def _portable_archive_path_allowed(cls, value: str) -> bool:
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            return False
        if len(path.parts) == 1:
            return path.name in PORTABLE_IMPORT_FILES
        return (
            len(path.parts) == 2
            and path.parts[0] == ATTACHMENT_DIRECTORY
            and cls._safe_attachment_storage_name(path.parts[1]) is not None
        )

    @classmethod
    def _changeset_attachment_names(cls, changeset: dict) -> set[str]:
        names: set[str] = set()
        for attachment in changeset.get("snapshot", {}).get("attachments") or []:
            if not isinstance(attachment, dict):
                raise ValueError("attachment metadata must be an object")
            storage_name = cls._safe_attachment_storage_name(str(attachment.get("storage_name") or ""))
            if not storage_name:
                raise ValueError("attachment storage_name is invalid")
            if attachment.get("owner_type") not in {"task", "event"} or not attachment.get("owner_id"):
                raise ValueError(f"attachment owner is invalid: {storage_name}")
            archive_name = f"{ATTACHMENT_DIRECTORY}/{storage_name}"
            if archive_name in names:
                raise ValueError(f"duplicate attachment storage_name: {storage_name}")
            names.add(archive_name)
        return names

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

    @staticmethod
    def _safe_attachment_id(value: str) -> str | None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", value or ""):
            return None
        return value

    @staticmethod
    def _safe_attachment_storage_name(value: str) -> str | None:
        if not value or Path(value).name != value:
            return None
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}\.[A-Za-z0-9]{1,8}", value):
            return None
        if Path(value).suffix.lower() not in ATTACHMENT_EXTENSIONS:
            return None
        return value

    @staticmethod
    def _attachment_url(storage_name: str) -> str:
        return f"/api/gantt-attachments/{quote(storage_name)}"

    def _route_path(self) -> str:
        return urlsplit(self.path).path.rstrip("/") or "/"


def _load_portable_exporter():
    spec = importlib.util.spec_from_file_location("export_gantt_portable", PORTABLE_EXPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {PORTABLE_EXPORT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.export_portable


def prepare_directory_from_portable(directory: Path, portable_directory: Path = PORTABLE_DIRECTORY) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in ["gantt.html", "gantt.json", "gantt-local-edits.json"]:
        source = portable_directory / name
        target = directory / name
        if source.exists() and not target.exists() and source.resolve() != target.resolve():
            shutil.copy2(source, directory / name)
    source_attachments = portable_directory / ATTACHMENT_DIRECTORY
    target_attachments = directory / ATTACHMENT_DIRECTORY
    if source_attachments.is_dir() and source_attachments.resolve() != target_attachments.resolve():
        target_attachments.mkdir(parents=True, exist_ok=True)
        for source in source_attachments.iterdir():
            if source.is_file() and DeliveryHandler._safe_attachment_storage_name(source.name):
                target = target_attachments / source.name
                if not target.exists():
                    shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve delivery exports with a local Gantt changeset API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
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
