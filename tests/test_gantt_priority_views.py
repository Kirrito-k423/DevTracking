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


class GanttPriorityViewTests(unittest.TestCase):
    def test_priority_view_controls_and_storage_fields_exist(self):
        html = GANTT_HTML.read_text(encoding="utf-8")
        self.assertIn('data-demand-lane="version_must"', html)
        self.assertIn('data-demand-lane="tech_prebuild"', html)
        self.assertIn("版本必做", html)
        self.assertIn("预埋技术", html)
        self.assertIn("demand_lane: taskDemandLane(task)", html)
        self.assertIn("pinned: Boolean(task.pinned)", html)
        self.assertIn("pin_position:", html)
        self.assertIn("className = 'task-pin'", html)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the inline JavaScript behavior test")
    def test_lane_default_freshness_sort_and_pin_slots(self):
        html = GANTT_HTML.read_text(encoding="utf-8")
        functions = "\n".join(
            extract_javascript_function(html, name)
            for name in (
                "taskDemandLane",
                "sortTasksByFreshnessWithPins",
                "prioritizedTasksForLane",
            )
        )
        task_list = [
            {"id": "old", "score": 1},
            {"id": "old-child", "parent_id": "old", "score": 2},
            {"id": "fixed", "score": 0, "pinned": True, "pin_position": 1},
            {"id": "recent", "score": 10},
            {"id": "tech", "score": 20, "demand_lane": "tech_prebuild"},
        ]
        script = f"""
const DEMAND_LANES = {{version_must:'版本必做', tech_prebuild:'预埋技术'}};
const activeDemandLane = 'version_must';
const tasks = [];
const events = [];
function eventsByTask() {{ return new Map(); }}
function latestTaskEventOrd(task) {{ return task.score; }}
{functions}
const sample = {json.dumps(task_list)};
const versionOrder = prioritizedTasksForLane('version_must', sample, []).map(task => task.id);
const techOrder = prioritizedTasksForLane('tech_prebuild', sample, []).map(task => task.id);
const expectedVersion = ['recent', 'fixed', 'old', 'old-child'];
if (JSON.stringify(versionOrder) !== JSON.stringify(expectedVersion)) {{
  throw new Error(`unexpected version order: ${{JSON.stringify(versionOrder)}}`);
}}
if (JSON.stringify(techOrder) !== JSON.stringify(['tech'])) {{
  throw new Error(`unexpected tech order: ${{JSON.stringify(techOrder)}}`);
}}
if (taskDemandLane({{id:'legacy'}}) !== 'version_must') {{
  throw new Error('legacy task did not default to version_must');
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
