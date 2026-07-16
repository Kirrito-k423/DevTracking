from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import threading
import types
import unittest
import urllib.request
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_script(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


server_module = load_script("delivery_server", "serve-delivery-dashboard.py")
progress_module = load_script("progress_to_plane", "progress-to-plane.py")
timeline_module = load_script("export_plane_timeline", "export-plane-timeline.py")
portable_module = load_script("export_gantt_portable", "export-gantt-portable.py")
daily_module = load_script("apply_plane_daily_record", "apply-plane-daily-record.py")
gantt_app_module = load_script("gantt_desktop_app", "gantt_app.py")


class QuietDeliveryHandler(server_module.DeliveryHandler):
    def log_message(self, format, *args):  # noqa: A002 - inherited API name
        return


class WindowsCompatibilityTests(unittest.TestCase):
    def test_runtime_data_can_live_outside_repository(self):
        with tempfile.TemporaryDirectory(prefix="devtracking windows ") as temp_dir:
            temp_root = Path(temp_dir)
            delivery_dir = temp_root / "delivery data"
            portable_dir = temp_root / "portable data"
            shutil.copytree(ROOT / "portable/gantt/latest", portable_dir)
            QuietDeliveryHandler.portable_directory = portable_dir
            server_module.prepare_directory_from_portable(delivery_dir, portable_dir)

            def handler(*args, **kwargs):
                return QuietDeliveryHandler(*args, directory=str(delivery_dir), **kwargs)

            server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with urllib.request.urlopen(base_url + "/gantt.html", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                with urllib.request.urlopen(base_url + "/api/gantt-portable/latest?t=windows", timeout=5) as response:
                    self.assertEqual(response.status, 200)

                changeset = {
                    "schema": "plane-demand-hub.gantt-edits.v1",
                    "snapshot": {"tasks": [], "events": []},
                }
                for route in ("gantt-autosave", "gantt-edits"):
                    body = json.dumps({"filename": "windows smoke.json", "changeset": changeset}).encode("utf-8")
                    request = urllib.request.Request(
                        base_url + "/api/" + route,
                        data=body,
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(request, timeout=5) as response:
                        payload = json.load(response)
                    self.assertTrue(payload["ok"])
                    self.assertTrue(Path(payload["path"]).is_absolute())
                    self.assertTrue(Path(payload["latest"]).is_absolute())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_progress_export_uses_current_python_interpreter(self):
        timeline = ROOT / "exports/plane/windows-test.jsonl"
        with mock.patch.object(progress_module.subprocess, "run") as run:
            progress_module.run_export(timeline)
        command = run.call_args.args[0]
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(Path(command[1]).name, "export-plane-timeline.py")
        self.assertIn(str(timeline), command)

    def test_python_child_tools_use_current_interpreter(self):
        with mock.patch.object(daily_module.subprocess, "run") as run:
            daily_module.run_bootstrap()
        bootstrap_command = run.call_args.args[0]
        self.assertEqual(bootstrap_command[0], sys.executable)
        self.assertEqual(Path(bootstrap_command[1]).name, "bootstrap-plane-visual-constructs.py")

        result = {
            "planned_plane_changes": [
                {
                    "change_id": "windows-test",
                    "operation": "plane_api_comment",
                    "mode": "apply_ready",
                    "target": {"workspace_slug": "test", "project_id": "project", "issue_id": "issue"},
                    "body": "test",
                    "external_id": "windows-test",
                }
            ],
            "skipped_changes": [],
            "applied_changes": [],
        }
        completed = types.SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch.dict(progress_module.os.environ, {"PLANE_API_KEY": "test-only"}), mock.patch.object(
            progress_module.subprocess, "run", return_value=completed
        ) as run:
            self.assertEqual(progress_module.apply_changes(result, dry_run=False), 0)
        comment_command = run.call_args.args[0]
        self.assertEqual(comment_command[0], sys.executable)
        self.assertEqual(Path(comment_command[1]).name, "plane-api-comment.py")

    def test_native_timeline_export_reuses_read_only_query(self):
        query = timeline_module.timeline_query()
        self.assertIn("begin read only;", query.lower())
        self.assertIn("copy (", query.lower())
        self.assertIn("commit;", query.lower())
        self.assertNotIn("<<'SQL'", query)

    def test_committed_windows_launchers_match_export_templates(self):
        portable = ROOT / "portable/gantt/latest"
        self.assertEqual((portable / "start-windows.bat").read_text(encoding="utf-8"), portable_module.windows_bat())
        self.assertEqual((portable / "start-windows.ps1").read_text(encoding="utf-8"), portable_module.windows_ps1())

    def test_desktop_seed_copy_includes_attachment_directory(self):
        with tempfile.TemporaryDirectory(prefix="gantt desktop seed ") as temp_dir:
            root = Path(temp_dir)
            seed = root / "portable/gantt/latest"
            seed.mkdir(parents=True)
            seed.joinpath("gantt-local-edits.json").write_text("{}", encoding="utf-8")
            attachment_dir = seed / "gantt-attachments"
            attachment_dir.mkdir()
            attachment_dir.joinpath("att-test.txt").write_text("desktop attachment", encoding="utf-8")
            target = root / "runtime/portable/gantt/latest"

            gantt_app_module.copy_seed_portable(root, target)

            self.assertEqual(
                (target / "gantt-attachments/att-test.txt").read_text(encoding="utf-8"),
                "desktop attachment",
            )

    def test_pyinstaller_spec_resolves_repository_from_spec_path(self):
        spec_path = ROOT / "packaging/plane-demand-hub-gantt.spec"
        captured_analysis = {}

        def analysis(*args, **kwargs):
            captured_analysis.update(kwargs)
            return types.SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])

        namespace = {
            "SPEC": str(spec_path),
            "Analysis": analysis,
            "PYZ": lambda *args, **kwargs: object(),
            "EXE": lambda *args, **kwargs: object(),
        }
        exec(compile(spec_path.read_text(encoding="utf-8"), str(spec_path), "exec"), namespace)
        self.assertEqual(namespace["ROOT"], ROOT)
        for source, _destination in namespace["datas"]:
            self.assertTrue(Path(source).is_file(), source)
        self.assertIn("json", captured_analysis["hiddenimports"])
        self.assertIn("http.server", captured_analysis["hiddenimports"])
        self.assertIn("hashlib", captured_analysis["hiddenimports"])
        self.assertIn("mimetypes", captured_analysis["hiddenimports"])


if __name__ == "__main__":
    unittest.main()
