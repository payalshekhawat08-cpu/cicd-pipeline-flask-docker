#!/usr/bin/env bash
# Deploy stage: build the image, start the container, wait until it is healthy.
set -euo pipefail

docker compose up -d --build

echo "Waiting for container cicd-demo-app to become healthy..."
for i in $(seq 1 30); do
  status=$(docker inspect --format '{{.State.Health.Status}}' cicd-demo-app 2>/dev/null || echo "starting")
  echo "  attempt $i: $status"
  if [ "$status" = "healthy" ]; then
    echo "Deploy OK: cicd-demo-app is healthy on http://localhost:8080"
    exit 0
  fi
  sleep 2
done

echo "Deploy FAILED: container did not become healthy" >&2
docker compose logs --tail 50 >&2
exit 1
