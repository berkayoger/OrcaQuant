#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

if [ ! -f "${FRONTEND_DIR}/package.json" ]; then
  echo "No frontend/package.json found, skipping frontend smoke checks."
  exit 0
fi

cd "$FRONTEND_DIR"

if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

npm run lint --if-present
npm test --if-present
npm run build --if-present
