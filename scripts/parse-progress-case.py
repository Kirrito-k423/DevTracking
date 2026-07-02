#!/usr/bin/env python3
"""Parse a small Chinese daily progress update into dry-run Plane changes."""

from __future__ import annotations

import argparse
import json
import sys

from progress_lib import parse_update


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse daily progress text into dry-run Plane changes.")
    parser.add_argument("text", nargs="?", help="Progress text. Reads stdin when omitted.")
    parser.add_argument("--source-id", default="manual-2026-07-02-001", help="Stable source id for traceability.")
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    text = text.strip()
    if not text:
        print("No progress text provided.", file=sys.stderr)
        return 2

    result = parse_update(text, args.source_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
