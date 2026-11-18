#!/usr/bin/env bash
# Monitor stage: check container state, health endpoint, metrics and recent logs.
set -euo pipefail

URL="http://localhost:8080"

echo "== Container state =="
state=$(docker inspect --format '{{.State.Status}} / {{.State.Health.Status}}' cicd-demo-app)
echo "$state"
if [ "$state" != "running / healthy" ]; then
  echo "Monitor FAILED: container is not running and healthy" >&2
  exit 1
fi

echo "== GET /health =="
curl -fsS "$URL/health"

echo "== GET /metrics =="
curl -fsS "$URL/metrics"

echo "== Last 10 log lines =="
docker compose logs --tail 10 --no-color

echo "Monitor OK"
