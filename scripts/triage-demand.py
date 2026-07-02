#!/usr/bin/env python3
"""Local demand triage and lightweight capability matching."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
ASCII_RE = re.compile(r"[a-zA-Z0-9]+")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokens(text: str) -> set[str]:
    ascii_tokens = {item.lower() for item in ASCII_RE.findall(text)}
    keywords = {kw for kw in ["SFT", "chunkmoe", "性能", "优化", "开发", "交付", "排队"] if kw.lower() in text.lower()}
    return ascii_tokens | {kw.lower() for kw in keywords}


def load_dashboard(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"people": [], "projects": []}
    return json.loads(path.read_text(encoding="utf-8"))


def infer_capabilities(dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    people = []
    for person in dashboard.get("people", []):
        skill_counts: Counter[str] = Counter()
        work_history = []
        for item in person.get("work_items", []):
            work = item.get("work_item") or ""
            work_history.append(item)
            for token in tokens(work):
                skill_counts[token] += 1
        blockers = len(person.get("blockers", []))
        people.append(
            {
                "person": person.get("person"),
                "skills": dict(skill_counts),
                "work_history": work_history,
                "current_load": person.get("events", 0),
                "blockers": blockers,
                "availability": max(0, 5 - blockers - max(0, person.get("events", 0) - 1)),
            }
        )
    return people


def category_for(text: str) -> str:
    if "性能" in text or "优化" in text:
        return "performance"
    if "SFT" in text or "模型" in text or "chunkmoe" in text.lower():
        return "model-delivery"
    if "需求" in text:
        return "requirement"
    return "general"


def score_requirement(text: str) -> dict[str, int]:
    return {
        "clarity": min(5, 1 + (len(text) // 12) + int("项目" in text) + int(bool(tokens(text)))),
        "value": 5 if any(k in text for k in ["交付", "客户", "关键", "影响"]) else 3,
        "urgency": 5 if any(k in text for k in ["紧急", "优先级高", "今天", "马上"]) else 3,
        "cost": 4 if any(k in text for k in ["新增", "开发", "实现"]) else 2,
        "risk": 5 if any(k in text for k in ["风险", "阻塞", "影响", "排队"]) else 2,
        "dependency": 4 if any(k in text for k in ["依赖", "等待", "排队"]) else 2,
        "strategic_fit": 4 if any(k in text for k in ["浦江", "交付", "SFT"]) else 3,
    }


def rank_score(scores: dict[str, int]) -> int:
    return scores["value"] * 2 + scores["urgency"] + scores["risk"] + scores["strategic_fit"] - scores["cost"] - scores["dependency"]


def project_hint(text: str) -> str | None:
    match = re.search(r"([^，,。；;\s]+项目)", text)
    if match:
        return match.group(1)
    if "浦江" in text:
        return "浦江"
    return None


def recommend(text: str, capabilities: list[dict[str, Any]]) -> dict[str, Any]:
    req_tokens = tokens(text)
    candidates = []
    for person in capabilities:
        skill_tokens = set(person.get("skills", {}).keys())
        overlap = req_tokens & skill_tokens
        score = len(overlap) * 3 + person.get("availability", 0)
        if any(token in skill_tokens for token in ["排队"]):
            score -= 1
        candidates.append(
            {
                "person": person["person"],
                "score": score,
                "confidence": min(95, max(25, score * 12)),
                "reasoning": [
                    f"skill_overlap={sorted(overlap)}",
                    f"availability={person.get('availability', 0)}",
                    f"blockers={person.get('blockers', 0)}",
                ],
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["person"] or ""))
    return candidates[0] if candidates else {"person": None, "score": 0, "confidence": 0, "reasoning": ["no people evidence"]}


def triage(requirements: list[str], source: str, dashboard: dict[str, Any]) -> dict[str, Any]:
    capabilities = infer_capabilities(dashboard)
    items = []
    planned_changes = []
    for index, text in enumerate(requirements, start=1):
        scores = score_requirement(text)
        status = "bounced" if scores["clarity"] < 3 else "approved_draft"
        recommendation = recommend(text, capabilities)
        item = {
            "id": f"demand-{index}",
            "source": source,
            "context": project_hint(text),
            "text": text,
            "category": category_for(text),
            "scores": scores,
            "rank_score": rank_score(scores),
            "status": status,
            "decision_notes": "需求不够清晰，需要补充目标、影响范围和验收标准。" if status == "bounced" else "进入候选 backlog，等待确认后创建 Plane work item。",
            "recommended_assignee": recommendation,
        }
        items.append(item)
        if status != "bounced":
            planned_changes.append(
                {
                    "operation": "create_plane_work_item_draft",
                    "mode": "draft",
                    "project_hint": item["context"],
                    "title": text[:80],
                    "category": item["category"],
                    "recommended_assignee": recommendation,
                    "source_demand_id": item["id"],
                }
            )
    items.sort(key=lambda item: -item["rank_score"])
    return {
        "generated_at": now(),
        "requirements": items,
        "capability_matrix": capabilities,
        "planned_plane_changes": planned_changes,
    }


def write_outputs(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "demand-backlog.json").write_text(json.dumps(result["requirements"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "capability-matrix.json").write_text(json.dumps(result["capability_matrix"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "planned-plane-changes.json").write_text(json.dumps(result["planned_plane_changes"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# Demand Triage", "", f"Generated: {result['generated_at']}", ""]
    for item in result["requirements"]:
        lines.append(f"## {item['id']}: {item['text']}")
        lines.append(f"- status: {item['status']}")
        lines.append(f"- category: {item['category']}")
        lines.append(f"- rank_score: {item['rank_score']}")
        lines.append(f"- scores: {item['scores']}")
        lines.append(f"- decision: {item['decision_notes']}")
        rec = item["recommended_assignee"]
        lines.append(f"- recommended_assignee: {rec.get('person')} ({rec.get('confidence')}%)")
        lines.append(f"- reasoning: {'; '.join(rec.get('reasoning', []))}")
        lines.append("")
    (output_dir / "triage.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage demand and recommend assignees.")
    parser.add_argument("--requirement", action="append", required=True, help="Requirement text; can be repeated.")
    parser.add_argument("--source", default="manual")
    parser.add_argument("--dashboard", default=str(ROOT_DIR / "exports/delivery/dashboard.json"))
    parser.add_argument("--output-dir", default=str(ROOT_DIR / "exports/demand"))
    args = parser.parse_args()

    result = triage(args.requirement, args.source, load_dashboard(Path(args.dashboard)))
    write_outputs(result, Path(args.output_dir))
    print(f"Wrote demand outputs to {args.output_dir}")
    print(json.dumps({"requirements": len(result["requirements"]), "planned_changes": len(result["planned_plane_changes"]), "people": len(result["capability_matrix"])}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

