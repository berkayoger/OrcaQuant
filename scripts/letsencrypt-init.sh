#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/deploy"

if [ ! -f ../.env ]; then
  echo "ERROR: .env yok. APP_DOMAIN ve LE_EMAIL doldurun."
  exit 1
fi
source ../.env

if [ -z "${APP_DOMAIN:-}" ]; then echo "APP_DOMAIN gerekli"; exit 1; fi
LE_EMAIL="${1:-${LE_EMAIL:-}}"
if [ -z "$LE_EMAIL" ]; then echo "LE_EMAIL gerekli (argüman olarak geçebilir)"; exit 1; fi

docker run --rm -it \
  -v certs:/etc/letsencrypt \
  -v certs-data:/var/lib/letsencrypt \
  -v $(pwd)/nginx/conf.d:/etc/nginx/conf.d \
  certbot/certbot certonly --standalone \
  --email "$LE_EMAIL" --agree-tos -d "$APP_DOMAIN"

docker compose -f docker-compose.prod.yml restart nginx
echo "SSL hazır. Sertifikalar yenileme için cron eklemeyi unutmayın."
