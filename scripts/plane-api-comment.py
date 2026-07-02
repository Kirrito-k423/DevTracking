#!/usr/bin/env python3
"""Create or update a Plane work-item comment through the Plane API."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.request


def comment_json(text: str) -> dict:
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def build_url(base_url: str, workspace_slug: str, project_id: str, issue_id: str, comment_id: str | None) -> str:
    base = base_url.rstrip("/")
    url = f"{base}/api/v1/workspaces/{workspace_slug}/projects/{project_id}/work-items/{issue_id}/comments/"
    if comment_id:
        url = f"{url}{comment_id}/"
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description="Plane API comment writer. Defaults to dry-run.")
    parser.add_argument("--base-url", default=os.environ.get("PLANE_URL", "http://localhost:8090"))
    parser.add_argument("--workspace", required=True, help="Plane workspace slug")
    parser.add_argument("--project-id", required=True, help="Plane project UUID")
    parser.add_argument("--issue-id", required=True, help="Plane work item UUID")
    parser.add_argument("--comment-id", help="Existing comment UUID. When provided, PATCH is used.")
    parser.add_argument("--comment", required=True, help="Plain text comment body")
    parser.add_argument("--access", default="INTERNAL")
    parser.add_argument("--external-source", default="plane-demand-hub")
    parser.add_argument("--external-id", help="Stable external id for idempotency")
    parser.add_argument("--apply", action="store_true", help="Actually call Plane API. Requires PLANE_API_KEY.")
    args = parser.parse_args()

    body = {
        "comment_html": f"<p>{html.escape(args.comment)}</p>",
        "comment_json": comment_json(args.comment),
        "access": args.access,
        "external_source": args.external_source,
    }
    if args.external_id:
        body["external_id"] = args.external_id

    url = build_url(args.base_url, args.workspace, args.project_id, args.issue_id, args.comment_id)
    method = "PATCH" if args.comment_id else "POST"

    preview = {
        "mode": "apply" if args.apply else "dry_run",
        "method": method,
        "url": url,
        "headers": {"X-Api-Key": "required; redacted"},
        "body": body,
        "write_boundary": "Plane API only. This script never writes Plane PostgreSQL directly.",
    }

    if not args.apply:
        print(json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    api_key = os.environ.get("PLANE_API_KEY")
    if not api_key:
        print("PLANE_API_KEY is required for --apply.", file=sys.stderr)
        return 2

    request = urllib.request.Request(
        url=url,
        data=json.dumps(body).encode("utf-8"),
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
            print(payload)
            return 0 if 200 <= response.status < 300 else 1
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        print(f"Plane API request failed: HTTP {exc.code}", file=sys.stderr)
        print(payload[:2000], file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Plane API request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

