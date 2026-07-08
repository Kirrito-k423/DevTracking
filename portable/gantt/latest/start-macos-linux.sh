#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
echo "Starting Plane Demand Hub Gantt at http://127.0.0.1:8091/gantt.html"
python3 scripts/serve-delivery-dashboard.py --host 127.0.0.1 --port 8091
