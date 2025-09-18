#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM_DIR="${ROOT_DIR}/nginx/upstreams"
cd "$UPSTREAM_DIR"

target="${1:-blue}" # blue|green
case "$target" in
  blue|green) ;;
  *) echo "usage: $0 [blue|green]"; exit 1 ;;
esac

cp "api_${target}.conf" active_api.conf
echo "[switch] Active upstream -> ${target}"
docker compose -f "${ROOT_DIR}/docker-compose.prod.yml" exec -T nginx nginx -s reload
echo "[switch] Nginx reloaded."
