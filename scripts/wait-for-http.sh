#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://127.0.0.1:8000/healthz}"
ATTEMPTS="${2:-60}"
SLEEP_SECS="${3:-2}"
for i in $(seq 1 "$ATTEMPTS"); do
  if curl -fsS "$URL" >/dev/null 2>&1; then
    echo "Service is up: $URL"
    exit 0
  fi
  echo "[$i/$ATTEMPTS] waiting $SLEEP_SECS s for $URL ..."
  sleep "$SLEEP_SECS"
done
echo "Timeout waiting for $URL"
exit 1

