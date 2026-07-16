from __future__ import annotations

import importlib.util
import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


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


server_module = load_script("delivery_server_attachments", "serve-delivery-dashboard.py")
portable_module = load_script("portable_exporter_attachments", "export-gantt-portable.py")


class QuietDeliveryHandler(server_module.DeliveryHandler):
    def log_message(self, format, *args):  # noqa: A002 - inherited API name
        return


class RunningServer:
    def __init__(self, delivery_dir: Path, portable_dir: Path):
        QuietDeliveryHandler.portable_directory = portable_dir

        def handler(*args, **kwargs):
            return QuietDeliveryHandler(*args, directory=str(delivery_dir), **kwargs)

        self.server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def request_json(url: str, data: bytes, method: str = "POST") -> dict:
    request = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


class GanttAttachmentTests(unittest.TestCase):
    def test_attachment_upload_read_delete_and_validation(self):
        with tempfile.TemporaryDirectory(prefix="gantt-attachments-") as temp_dir:
            root = Path(temp_dir)
            delivery = root / "delivery"
            portable = root / "portable"
            delivery.mkdir()
            portable.mkdir()
            with RunningServer(delivery, portable) as running:
                query = urllib.parse.urlencode({
                    "id": "att-test-image",
                    "name": "示例图片.png",
                    "content_type": "image/png",
                })
                payload = request_json(
                    f"{running.base_url}/api/gantt-attachments?{query}",
                    b"\x89PNG\r\n\x1a\nattachment-test",
                )
                attachment = payload["attachment"]
                self.assertEqual(attachment["storage_name"], "att-test-image.png")
                self.assertEqual(attachment["size"], 23)

                with urllib.request.urlopen(running.base_url + attachment["url"], timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.headers.get_content_type(), "image/png")
                    self.assertEqual(response.read(), b"\x89PNG\r\n\x1a\nattachment-test")

                bad_query = urllib.parse.urlencode({"id": "att-bad", "name": "payload.exe"})
                with self.assertRaises(urllib.error.HTTPError) as invalid_type:
                    request_json(f"{running.base_url}/api/gantt-attachments?{bad_query}", b"bad")
                self.assertEqual(invalid_type.exception.code, 415)
                invalid_type.exception.close()

                large_query = urllib.parse.urlencode({"id": "att-large", "name": "large.zip"})
                connection = http.client.HTTPConnection("127.0.0.1", running.server.server_address[1], timeout=5)
                connection.putrequest("POST", f"/api/gantt-attachments?{large_query}")
                connection.putheader("Content-Length", str(server_module.ATTACHMENT_MAX_BYTES + 1))
                connection.endheaders()
                response = connection.getresponse()
                self.assertEqual(response.status, 413)
                response.read()
                connection.close()

                delete_request = urllib.request.Request(
                    running.base_url + attachment["url"],
                    method="DELETE",
                )
                with urllib.request.urlopen(delete_request, timeout=5) as response:
                    deleted = json.load(response)
                self.assertTrue(deleted["ok"])
                self.assertTrue(deleted["deleted"])
                self.assertFalse((delivery / "gantt-attachments/att-test-image.png").exists())

    def test_portable_zip_round_trip_keeps_bound_attachments(self):
        with tempfile.TemporaryDirectory(prefix="gantt-portable-attachments-") as temp_dir:
            root = Path(temp_dir)
            source_delivery = root / "source-delivery"
            source_portable = root / "source-portable"
            source_delivery.mkdir()
            source_delivery.joinpath("gantt.html").write_text("<html>gantt</html>", encoding="utf-8")
            source_delivery.joinpath("gantt.json").write_text(
                json.dumps({"generated_at": "2026-07-16T00:00:00Z", "tasks": [], "events": []}),
                encoding="utf-8",
            )
            attachment_dir = source_delivery / "gantt-attachments"
            attachment_dir.mkdir()
            attachment_dir.joinpath("att-report.txt").write_text("portable attachment", encoding="utf-8")
            changeset = {
                "schema": "plane-demand-hub.gantt-edits.v1",
                "generated_at": "2026-07-16T00:00:00Z",
                "snapshot": {
                    "tasks": [{"id": "task-1", "title": "Task"}],
                    "events": [],
                    "attachments": [{
                        "id": "att-report",
                        "owner_type": "task",
                        "owner_id": "task-1",
                        "name": "报告.txt",
                        "storage_name": "att-report.txt",
                        "content_type": "text/plain",
                        "size": 19,
                        "uploaded_at": "2026-07-16T00:00:00Z",
                    }],
                },
            }
            result = portable_module.export_portable(source_delivery, source_portable, changeset=changeset)
            self.assertEqual(result["manifest"]["counts"]["attachments"], 1)
            self.assertIn("gantt-attachments/att-report.txt", result["manifest"]["files"])

            with RunningServer(source_delivery, source_portable) as running:
                with urllib.request.urlopen(running.base_url + "/api/gantt-portable/download", timeout=10) as response:
                    package = response.read()
            with zipfile.ZipFile(io.BytesIO(package)) as archive:
                self.assertEqual(archive.read("gantt-attachments/att-report.txt"), b"portable attachment")

            target_delivery = root / "target-delivery"
            target_portable = root / "target-portable"
            target_delivery.mkdir()
            target_portable.mkdir()
            with RunningServer(target_delivery, target_portable) as running:
                imported = request_json(
                    running.base_url + "/api/gantt-portable/import",
                    package,
                )
                self.assertEqual(imported["counts"]["attachments"], 1)
                with urllib.request.urlopen(
                    running.base_url + "/api/gantt-attachments/att-report.txt",
                    timeout=5,
                ) as response:
                    self.assertEqual(response.read(), b"portable attachment")
            self.assertEqual(
                (target_delivery / "gantt-attachments/att-report.txt").read_text(encoding="utf-8"),
                "portable attachment",
            )
            self.assertEqual(
                (target_portable / "gantt-attachments/att-report.txt").read_text(encoding="utf-8"),
                "portable attachment",
            )


if __name__ == "__main__":
    unittest.main()
