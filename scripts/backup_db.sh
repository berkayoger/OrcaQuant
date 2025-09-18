#!/usr/bin/env bash
set -euo pipefail

# Production DB yedeği: PostgreSQL/MySQL/SQLite destekler.
# S3 varsa oraya yükler; yoksa çıktıyı artifacts olarak bırakır.

ts="$(date +%Y%m%d-%H%M%S)"
DB_URL="${DATABASE_URL:-}"
OUT_DIR="${OUT_DIR:-backup}"
mkdir -p "$OUT_DIR"

fail() { echo "ERR: $*" >&2; exit 1; }

if [[ -z "$DB_URL" ]]; then
  fail "DATABASE_URL boş. .env dosyanızı doldurun."
fi

case "$DB_URL" in
  postgresql*|postgres*)
    BIN="${PG_DUMP_BIN:-pg_dump}"
    FILE="$OUT_DIR/orcaquant-pg-$ts.sql.gz"
    echo "-> PostgreSQL yedeği alınıyor: $FILE"
    "$BIN" --no-owner --no-privileges --format=plain "$DB_URL" | gzip -9 > "$FILE"
    ;;
  mysql*|mariadb*)
    BIN="${MYSQLDUMP_BIN:-mysqldump}"
    FILE="$OUT_DIR/orcaquant-mysql-$ts.sql.gz"
    echo "-> MySQL/MariaDB yedeği alınıyor: $FILE"
    "$BIN" --single-transaction --routines --triggers "$DB_URL" | gzip -9 > "$FILE"
    ;;
  sqlite*|sqlite3*)
    FILE="$OUT_DIR/orcaquant-sqlite-$ts.sql.gz"
    DB_PATH="${DB_URL#sqlite:///}"
    [[ -f "$DB_PATH" ]] || fail "SQLite DB bulunamadı: $DB_PATH"
    echo "-> SQLite yedeği alınıyor: $FILE"
    sqlite3 "$DB_PATH" .dump | gzip -9 > "$FILE"
    ;;
  *)
    fail "Desteklenmeyen DB_URL şeması: $DB_URL"
    ;;
esac

if [[ -n "${AWS_S3_BACKUP_BUCKET:-}" && -n "${AWS_ACCESS_KEY_ID:-}" && -n "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
  echo "-> S3'ye yükleniyor: s3://$AWS_S3_BACKUP_BUCKET/"
  aws s3 cp "$FILE" "s3://$AWS_S3_BACKUP_BUCKET/"
else
  echo "-> S3 yapılandırılmadı; dosya yerelde kaldı: $FILE"
fi

echo "OK"
