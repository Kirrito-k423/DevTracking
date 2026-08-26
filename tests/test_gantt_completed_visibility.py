from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GANTT_HTML = ROOT / "portable/gantt/latest/gantt.html"


def extract_javascript_function(source: str, name: str) -> str:
    start = source.index(f"function {name}(")
    brace = source.index("{", start)
    depth = 0
    quote = None
    escaped = False
    for index in range(brace, len(source)):
        character = source[index]
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {"'", '"', "`"}:
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f"Unterminated JavaScript function: {name}")


class GanttCompletedVisibilityTests(unittest.TestCase):
    def test_toolbar_exposes_show_all_toggle(self):
        html = GANTT_HTML.read_text(encoding="utf-8")
        self.assertIn('id="show-all-tasks"', html)
        self.assertIn(">全部显示</button>", html)
        self.assertIn("showAllTasks = !showAllTasks", html)
        self.assertIn("if (showAllTasks) {\n        collapsed.clear();", html)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the inline JavaScript behavior test")
    def test_completed_parent_hides_its_descendants(self):
        html = GANTT_HTML.read_text(encoding="utf-8")
        functions = "\n".join(
            extract_javascript_function(html, name)
            for name in (
                "stateText",
                "isTaskCompleted",
                "isTaskHiddenByCompletion",
                "completedTaskAndDescendantIds",
            )
        )
        task_list = [
            {"id": "done-parent", "state": "Done", "progress": 0},
            {"id": "child", "parent_id": "done-parent", "state": "In Progress", "progress": 10},
            {"id": "grandchild", "parent_id": "child", "state": "Todo", "progress": 0},
            {"id": "progress-done", "state": "In Progress", "progress": 100},
            {"id": "timestamp-done", "state": "In Progress", "progress": 20, "completed_at": "2026-07-23"},
            {"id": "active", "state": "In Progress", "progress": 99},
        ]
        script = f"""
const text = value => value === null || value === undefined || value === '' ? 'n/a' : String(value);
const tasks = [];
const tasksById = new Map();
{functions}
const sample = {json.dumps(task_list)};
const actual = [...completedTaskAndDescendantIds(sample)].sort();
const expected = ['child', 'done-parent', 'grandchild', 'progress-done', 'timestamp-done'].sort();
if (JSON.stringify(actual) !== JSON.stringify(expected)) {{
  throw new Error(`unexpected hidden ids: ${{JSON.stringify(actual)}}`);
}}
"""
        result = subprocess.run(
            [shutil.which("node"), "-e", script],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
