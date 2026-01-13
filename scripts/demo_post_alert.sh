#!/usr/bin/env bash
# Demo: postear una alerta de ejemplo al orchestrator
set -eu
ORCH=${1:-http://localhost:8000}
CAM=${2:-cam-demo-1}
echo "Posting demo alert to ${ORCH} (camera=${CAM})"
PAYLOAD=$(cat <<'JSON'
{
  "camera_id": "CAM_ID_REPLACE",
  "metadata": {"detections":[{"bbox":[10,20,120,90],"confidence":0.95,"label":"zorro"}]},
  "thumbnail_b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIW2P4z8DwHwAF/gJ+RMR3VQAAAABJRU5ErkJggg=="
}
JSON
)

PAYLOAD=${PAYLOAD//CAM_ID_REPLACE/${CAM}}
curl -s -X POST "$ORCH/alert" -H 'Content-Type: application/json' -d "$PAYLOAD" -w "\nHTTP:%{http_code}\n"

echo "Done. Use the dashboard visual: http://localhost:8200/visual or via proxy https://localhost/"
