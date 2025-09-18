#!/usr/bin/env bash
set -euo pipefail
# Basit geri yükleme aracı
FILE="${1:-}"
DB_URL="${DATABASE_URL:-}"
[[ -f "$FILE" ]] || { echo "Kullanım: $0 <backup.sql.gz>"; exit 2; }
[[ -n "$DB_URL" ]] || { echo "DATABASE_URL boş."; exit 2; }

case "$DB_URL" in
  postgresql*|postgres*)
    gunzip -c "$FILE" | psql "$DB_URL"
    ;;
  mysql*|mariadb*)
    gunzip -c "$FILE" | mysql "$DB_URL"
    ;;
  sqlite*|sqlite3*)
    DB_PATH="${DB_URL#sqlite:///}"
    sqlite3 "$DB_PATH" < <(gunzip -c "$FILE")
    ;;
  *)
    echo "Desteklenmeyen DB_URL: $DB_URL"
    exit 3
    ;;
esac
echo "Geri yükleme tamam."
