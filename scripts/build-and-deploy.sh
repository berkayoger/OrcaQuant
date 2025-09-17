#!/usr/bin/env bash
set -euo pipefail

echo "[OrcaQuant] Frontend Build & Deploy"

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
FRONTEND_DIR="${FRONTEND_DIR:-$REPO_DIR/frontend/spa}"
STATIC_DIR="${STATIC_DIR:-$REPO_DIR/backend/static}"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "Frontend directory bulunamadı: $FRONTEND_DIR" >&2
  exit 1
fi

cd "$FRONTEND_DIR"

echo ">> npm ci"
npm ci

echo ">> npm run build"
npm run build

if [[ ! -d "dist" ]]; then
  echo "Vite build çıktısı (dist) bulunamadı" >&2
  exit 1
fi

mkdir -p "$STATIC_DIR"

echo ">> Statikleri backend/static altına kopyala"
rm -rf "$STATIC_DIR"/*
cp -r dist/* "$STATIC_DIR"/

if command -v docker-compose >/dev/null 2>&1; then
  echo ">> Docker rebuild"
  docker-compose -f "$REPO_DIR/docker-compose.yml" build --no-cache backend
  docker-compose -f "$REPO_DIR/docker-compose.yml" up -d
else
  echo ">> Docker-compose bulunamadı, yalnızca dosyalar güncellendi."
fi

echo "[OrcaQuant] Deploy tamamlandı!"
